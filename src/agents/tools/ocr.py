from smolagents import tool
import cv2
import numpy as np
import httpx
import easyocr
import string
from difflib import SequenceMatcher

# Load these in memory for faster subsequent calls
reader = easyocr.Reader(['en'])
east_model = 'models/frozen_east_text_detection.pb'
net = cv2.dnn.readNet(east_model)


def enhance_contrast(image):
    """
    Enhance image contrast using CLAHE on the L-channel in LAB color space.
    This helps EasyOCR on low-contrast areas.
    """
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    merged = cv2.merge((cl, a, b))
    enhanced = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
    return enhanced


# @tool
def get_text_boxes(image_url: str, texts: list[str]) -> list[dict]:
    """
    Given an image URL (or file path) and a list of strings known to be in the image,
    returns a list of bounding boxes for exactly those texts.
    This version groups OCR detections vertically (to handle multiline text)
    and uses fuzzy matching to decide which combined group best matches the target text.
    """
    # ------------------
    # STEP 0: Download/load the image
    # ------------------
    if image_url.startswith('http'):
        response = httpx.get(image_url)
        response.raise_for_status()
        image_data = np.frombuffer(response.content, np.uint8)
    else:
        with open(image_url, 'rb') as f:
            data = f.read()
        image_data = np.frombuffer(data, np.uint8)
    image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
    orig_h, orig_w = image.shape[:2]

    # ------------------
    # STEP 1: Use OpenCV EAST to detect candidate text boxes
    # ------------------
    new_w, new_h = (orig_w // 32) * 32, (orig_h // 32) * 32
    resized = cv2.resize(image, (new_w, new_h))
    blob = cv2.dnn.blobFromImage(
        resized, 1.0, (new_w, new_h), (123.68, 116.78, 103.94),
        swapRB=True, crop=False
    )
    net.setInput(blob)
    layerNames = ["feature_fusion/Conv_7/Sigmoid", "feature_fusion/concat_3"]
    scores, geometry = net.forward(layerNames)
    boxes, confidences = decode_predictions(scores, geometry, scoreThresh=0.5)
    indices = cv2.dnn.NMSBoxes(
        [[b[0], b[1], b[2]-b[0], b[3]-b[1]] for b in boxes],
        confidences, 0.5, 0.4
    )
    candidate_boxes = []
    for i in indices:
        i = i[0] if isinstance(i, (list, tuple, np.ndarray)) else i
        (startX, startY, endX, endY) = boxes[i]
        scale_w = orig_w / new_w
        scale_h = orig_h / new_h
        startX = int(startX * scale_w)
        startY = int(startY * scale_h)
        endX = int(endX * scale_w)
        endY = int(endY * scale_h)
        candidate_boxes.append((startX, startY, endX - startX, endY - startY))

    # ------------------
    # STEP 2: Merge boxes and cluster them into len(texts) groups
    # ------------------
    merged_boxes = merge_boxes(candidate_boxes, overlapThresh=10)
    clusters = cluster_boxes(merged_boxes, len(texts))
    group_boxes = [enclosing_box(cluster) for cluster in clusters]

    # ------------------
    # STEP 3: Refine text detection with EasyOCR and flexible multiline matching
    # ------------------
    results = []
    padding = 5  # extra pixels for padding
    similarity_threshold = 0.85

    for group_box, target_text in zip(group_boxes, texts):
        gx, gy, gw, gh = group_box
        roi = image[gy:gy+gh, gx:gx+gw]
        roi_enhanced = enhance_contrast(roi)
        ocr_results = reader.readtext(roi_enhanced)

        # Normalize target text (lower-case, remove extra spaces)
        normalized_target = " ".join(target_text.lower().split())

        if not ocr_results:
            # If no OCR detections, fallback to group box.
            results.append({
                "text": target_text,
                "x": gx,
                "y": gy,
                "width": gw,
                "height": gh
            })
            continue

        # --- Group OCR detections by vertical proximity ---
        # Sort OCR detections by the top y coordinate.
        sorted_results = sorted(
            ocr_results, key=lambda item: min(pt[1] for pt in item[0]))
        groups = []
        current_group = []
        current_bottom = None
        vertical_gap_threshold = 15  # pixels
        for (bbox, ocr_text, conf) in sorted_results:
            top = min(pt[1] for pt in bbox)
            bottom = max(pt[1] for pt in bbox)
            if not current_group:
                current_group.append((bbox, ocr_text, conf))
                current_bottom = bottom
            else:
                if top - current_bottom < vertical_gap_threshold:
                    current_group.append((bbox, ocr_text, conf))
                    current_bottom = max(current_bottom, bottom)
                else:
                    groups.append(current_group)
                    current_group = [(bbox, ocr_text, conf)]
                    current_bottom = bottom
        if current_group:
            groups.append(current_group)

        # --- Evaluate each group candidate by concatenating their texts ---
        best_ratio = 0
        best_bbox = None
        for group in groups:
            # Concatenate texts in order (sorted by top coordinate within group)
            group_sorted = sorted(
                group, key=lambda item: min(pt[1] for pt in item[0]))
            group_text = " ".join(item[1].strip() for item in group_sorted)
            normalized_group_text = " ".join(group_text.lower().split())
            ratio = SequenceMatcher(
                None, normalized_target, normalized_group_text).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                # Union all bounding boxes in the group.
                all_points = []
                for (bbox, _, _) in group_sorted:
                    all_points.extend(bbox)
                best_bbox = all_points

        if best_bbox is not None and best_ratio >= similarity_threshold:
            xs = [pt[0] for pt in best_bbox]
            ys = [pt[1] for pt in best_bbox]
            bx = int(min(xs)) + gx - padding
            by = int(min(ys)) + gy - padding
            bx2 = int(max(xs)) + gx + padding
            by2 = int(max(ys)) + gy + padding
            results.append({
                "text": target_text,
                "x": bx,
                "y": by,
                "width": bx2 - bx,
                "height": by2 - by
            })
        else:
            # Fallback: if no candidate group sufficiently matches, use the entire group_box.
            results.append({
                "text": target_text,
                "x": gx,
                "y": gy,
                "width": gw,
                "height": gh
            })
    return results


def decode_predictions(scores, geometry, scoreThresh):
    boxes = []
    confidences = []
    (numRows, numCols) = scores.shape[2:4]
    for y in range(numRows):
        for x in range(numCols):
            score = scores[0, 0, y, x]
            if score < scoreThresh:
                continue
            offsetX, offsetY = x * 4.0, y * 4.0
            angle = geometry[0, 4, y, x]
            cos = np.cos(angle)
            sin = np.sin(angle)
            h_box = geometry[0, 0, y, x] + geometry[0, 2, y, x]
            w_box = geometry[0, 1, y, x] + geometry[0, 3, y, x]
            endX = int(
                offsetX + (cos * geometry[0, 1, y, x]) + (sin * geometry[0, 2, y, x]))
            endY = int(
                offsetY - (sin * geometry[0, 1, y, x]) + (cos * geometry[0, 2, y, x]))
            startX = int(endX - w_box)
            startY = int(endY - h_box)
            boxes.append((startX, startY, endX, endY))
            confidences.append(float(score))
    return boxes, confidences


def merge_boxes(boxes, overlapThresh=10):
    if not boxes:
        return []
    merged = []
    used = [False] * len(boxes)
    for i in range(len(boxes)):
        if used[i]:
            continue
        (x, y, w, h) = boxes[i]
        current_x1, current_y1 = x, y
        current_x2, current_y2 = x + w, y + h
        for j in range(i+1, len(boxes)):
            if used[j]:
                continue
            (bx, by, bw, bh) = boxes[j]
            bx1, by1 = bx, by
            bx2, by2 = bx + bw, by + bh
            if not (current_x2 < bx1 - overlapThresh or current_x1 > bx2 + overlapThresh or
                    current_y2 < by1 - overlapThresh or current_y1 > by2 + overlapThresh):
                current_x1 = min(current_x1, bx1)
                current_y1 = min(current_y1, by1)
                current_x2 = max(current_x2, bx2)
                current_y2 = max(current_y2, by2)
                used[j] = True
        merged.append((current_x1, current_y1, current_x2 -
                      current_x1, current_y2 - current_y1))
    return merged


def cluster_boxes(boxes, k):
    if len(boxes) == 0:
        return [[] for _ in range(k)]
    centroids = []
    for (x, y, w, h) in boxes:
        centroids.append([x + w / 2, y + h / 2])
    centroids = np.float32(centroids)
    if len(centroids) < k:
        clusters = [[box] for box in boxes]
        for _ in range(k - len(centroids)):
            clusters.append([])
        return clusters
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, _ = cv2.kmeans(
        centroids, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    clusters = [[] for _ in range(k)]
    for idx, label in enumerate(labels.flatten()):
        clusters[label].append(boxes[idx])
    return clusters


def enclosing_box(boxes):
    if not boxes:
        return (0, 0, 0, 0)
    xs = [box[0] for box in boxes]
    ys = [box[1] for box in boxes]
    xs2 = [box[0] + box[2] for box in boxes]
    ys2 = [box[1] + box[3] for box in boxes]
    return (min(xs), min(ys), max(xs2) - min(xs), max(ys2) - min(ys))
