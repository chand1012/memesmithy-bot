from src.agents.tools.ocr import get_text_boxes
import cv2
boxes = get_text_boxes(
    "./test2.jpg", ["OpenAI Sora Lectures", "everyone"])

# load the image and draw the boxes
image = cv2.imread("./test.jpg")
for box in boxes:
    cv2.rectangle(image, (box["x"], box["y"]), (box["x"] +
                  box["width"], box["y"] + box["height"]), (0, 0, 255), 2)
# save the image
cv2.imwrite("./test_boxes.jpg", image)
