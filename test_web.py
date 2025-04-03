# import cv2
# import httpx
# import os
# import numpy as np
# import easyocr

# from src.agents.tools import get_image_text

# reader = easyocr.Reader(['en'])


# def get_str_bounding_box(image_url: str, input_text: str) -> tuple[int, int, int, int]:
#     """
#     Given the URL of an image and a string, returns the bounding box of the string in the image.
#     Handles cases where the text might be split across multiple lines or split on spaces,
#     and also handles repeated words by considering spatial relationships.

#     Args:
#         image_url: The URL of the image to get the bounding box of.
#         input_text: The string to get the bounding box of.

#     Returns:
#         A tuple of the bounding box of the string in the image. (x, y, w, h)
#     """

#     resp = httpx.get(image_url)
#     resp.raise_for_status()

#     image = cv2.imdecode(np.frombuffer(
#         resp.content, np.uint8), cv2.IMREAD_COLOR)

#     results = reader.readtext(image)

#     # Clean the input text for comparison
#     input_text_clean = input_text.strip().lower()
#     input_words = input_text_clean.split()

#     # First try exact match
#     for (bbox, text, prob) in results:
#         text_clean = text.strip().lower()
#         if text_clean == input_text_clean:
#             # Exact match found
#             (x, y, w, h) = (bbox[0][0], bbox[0][1], bbox[2]
#                             [0] - bbox[0][0], bbox[2][1] - bbox[0][1])
#             return (int(x), int(y), int(w), int(h))

#     # If no exact match, we need to find the best combination of text segments
#     # that match our input text

#     # First, collect all text segments with their bounding boxes
#     text_segments = []
#     for (bbox, text, prob) in results:
#         text_clean = text.strip().lower()
#         # Calculate center point of the bounding box
#         center_x = (bbox[0][0] + bbox[2][0]) / 2
#         center_y = (bbox[0][1] + bbox[2][1]) / 2
#         text_segments.append({
#             'text': text_clean,
#             'bbox': bbox,
#             'center_x': center_x,
#             'center_y': center_y
#         })

#     # Sort text segments by y-coordinate (top to bottom)
#     text_segments.sort(key=lambda x: x['center_y'])

#     # Function to calculate distance between two text segments
#     def segment_distance(seg1, seg2):
#         return ((seg1['center_x'] - seg2['center_x'])**2 +
#                 (seg1['center_y'] - seg2['center_y'])**2)**0.5

#     # Function to check if a sequence of text segments matches our input text
#     def segments_match_input(segments):
#         combined_text = ' '.join(seg['text'] for seg in segments)
#         # Check if all words from input are in the combined text
#         for word in input_words:
#             if word not in combined_text:
#                 return False
#         return True

#     # Function to get bounding box for a sequence of segments
#     def get_combined_bbox(segments):
#         if not segments:
#             return None

#         min_x = float('inf')
#         min_y = float('inf')
#         max_x = float('-inf')
#         max_y = float('-inf')

#         for seg in segments:
#             bbox = seg['bbox']
#             min_x = min(min_x, bbox[0][0])
#             min_y = min(min_y, bbox[0][1])
#             max_x = max(max_x, bbox[2][0])
#             max_y = max(max_y, bbox[2][1])

#         width = max_x - min_x
#         height = max_y - min_y

#         return (int(min_x), int(min_y), int(width), int(height))

#     # Try to find the best sequence of text segments that match our input
#     best_match = None
#     best_score = float('inf')

#     # Try different window sizes (number of consecutive segments)
#     for window_size in range(1, min(len(text_segments) + 1, 10)):
#         # Slide the window through all possible positions
#         for i in range(len(text_segments) - window_size + 1):
#             window = text_segments[i:i+window_size]

#             # Check if this window matches our input text
#             if segments_match_input(window):
#                 # Calculate a score based on how well the segments match the input
#                 # Lower score is better
#                 combined_text = ' '.join(seg['text'] for seg in window)

#                 # Count how many words from input are in the combined text
#                 word_count = sum(
#                     1 for word in input_words if word in combined_text)

#                 # Calculate average distance between consecutive segments
#                 total_distance = 0
#                 for j in range(len(window) - 1):
#                     total_distance += segment_distance(window[j], window[j+1])
#                 avg_distance = total_distance / \
#                     (len(window) - 1) if len(window) > 1 else 0

#                 # Score is based on word count and average distance
#                 # We want to maximize word count and minimize distance
#                 score = -word_count + avg_distance / 100

#                 if score < best_score:
#                     best_score = score
#                     best_match = window

#     # If we found a match, return its bounding box
#     if best_match:
#         return get_combined_bbox(best_match)

#     # If we still haven't found a match, try a more aggressive approach
#     # Look for any text segments that contain any of the words from the input text
#     matching_boxes = []
#     for (bbox, text, prob) in results:
#         text_clean = text.strip().lower()
#         # Check if this text segment is part of our input text
#         if any(word in text_clean for word in input_words) or any(text_clean in word for word in input_words):
#             matching_boxes.append(bbox)

#     if matching_boxes:
#         # Find the min x, min y, max x, max y across all boxes
#         min_x = float('inf')
#         min_y = float('inf')
#         max_x = float('-inf')
#         max_y = float('-inf')

#         for bbox in matching_boxes:
#             min_x = min(min_x, bbox[0][0])
#             min_y = min(min_y, bbox[0][1])
#             max_x = max(max_x, bbox[2][0])
#             max_y = max(max_y, bbox[2][1])

#         # Calculate width and height
#         width = max_x - min_x
#         height = max_y - min_y

#         return (int(min_x), int(min_y), int(width), int(height))

#     raise Exception(f"Text not found in image: {input_text}")

# # load the images.txt file and create a directory to download the images
# # don't use their original names, use a counter instead


# images = []
# with open("images.txt", "r") as f:
#     for line in f.readlines():
#         images.append(line.strip())

# # loop through all the images and get the text boxes
# image_boxes = []
# for url in images:
#     print(f'Processing {url}')
#     texts = get_image_text(url)
#     boxes = []
#     for text in texts:
#         try:
#             boxes.append(get_str_bounding_box(url, text))
#         except Exception as e:
#             print(f'Error getting bounding box for {text}: {e}')
#     image_boxes.append(boxes)

# # make a directory called images_with_boxes
# os.makedirs("images_with_boxes", exist_ok=True)

# counter = 0
# # open each image and draw the boxes on it
# for url in images:
#     print(f'Adding boxes to {url}')
#     # download the image and load into opencv
#     resp = httpx.get(url)
#     resp.raise_for_status()
#     image = cv2.imdecode(np.frombuffer(
#         resp.content, np.uint8), cv2.IMREAD_COLOR)
#     for box in image_boxes[counter]:
#         cv2.rectangle(image, (box[0], box[1]), (box[0] +
#                       box[2], box[1] + box[3]), (0, 0, 255), 2)
#     cv2.imwrite(f"images_with_boxes/{counter}.jpg", image)
#     counter += 1

import numpy as np
import httpx
import cv2
google_api_response = {
    "responses": [
        {
            "textAnnotations": [
                {
                    "locale": "en",
                    "description": "WHO AM ICOOKING\nUPA FUNNY REPLY FOR\nSOME RANDOM ASS COMMENT\nimgflip.com",
                    "boundingPoly": {
                        "vertices": [
                            {
                              "x": 3,
                              "y": 8
                            },
                            {
                                "x": 485,
                                "y": 8
                            },
                            {
                                "x": 485,
                                "y": 674
                            },
                            {
                                "x": 3,
                                "y": 674
                            }
                        ]
                    }
                },
                {
                    "description": "WHO",
                    "boundingPoly": {
                        "vertices": [
                            {
                                "x": 77,
                                "y": 8
                            },
                            {
                                "x": 159,
                                "y": 8
                            },
                            {
                                "x": 159,
                                "y": 40
                            },
                            {
                                "x": 77,
                                "y": 40
                            }
                        ]
                    }
                },
                {
                    "description": "AM",
                    "boundingPoly": {
                        "vertices": [
                            {
                                "x": 177,
                                "y": 8
                            },
                            {
                                "x": 230,
                                "y": 8
                            },
                            {
                                "x": 230,
                                "y": 40
                            },
                            {
                                "x": 177,
                                "y": 40
                            }
                        ]
                    }
                },
                {
                    "description": "ICOOKING",
                    "boundingPoly": {
                        "vertices": [
                            {
                                "x": 253,
                                "y": 8
                            },
                            {
                                "x": 418,
                                "y": 8
                            },
                            {
                                "x": 418,
                                "y": 40
                            },
                            {
                                "x": 253,
                                "y": 40
                            }
                        ]
                    }
                },
                {
                    "description": "UPA",
                    "boundingPoly": {
                        "vertices": [
                            {
                                "x": 75,
                                "y": 52
                            },
                            {
                                "x": 149,
                                "y": 52
                            },
                            {
                                "x": 149,
                                "y": 86
                            },
                            {
                                "x": 75,
                                "y": 86
                            }
                        ]
                    }
                },
                {
                    "description": "FUNNY",
                    "boundingPoly": {
                        "vertices": [
                            {
                                "x": 155,
                                "y": 52
                            },
                            {
                                "x": 258,
                                "y": 52
                            },
                            {
                                "x": 258,
                                "y": 86
                            },
                            {
                                "x": 155,
                                "y": 86
                            }
                        ]
                    }
                },
                {
                    "description": "REPLY",
                    "boundingPoly": {
                        "vertices": [
                            {
                                "x": 263,
                                "y": 52
                            },
                            {
                                "x": 360,
                                "y": 52
                            },
                            {
                                "x": 360,
                                "y": 86
                            },
                            {
                                "x": 263,
                                "y": 86
                            }
                        ]
                    }
                },
                {
                    "description": "FOR",
                    "boundingPoly": {
                        "vertices": [
                            {
                                "x": 362,
                                "y": 52
                            },
                            {
                                "x": 424,
                                "y": 52
                            },
                            {
                                "x": 424,
                                "y": 86
                            },
                            {
                                "x": 362,
                                "y": 86
                            }
                        ]
                    }
                },
                {
                    "description": "SOME",
                    "boundingPoly": {
                        "vertices": [
                            {
                                "x": 6,
                                "y": 95
                            },
                            {
                                "x": 98,
                                "y": 95
                            },
                            {
                                "x": 98,
                                "y": 128
                            },
                            {
                                "x": 6,
                                "y": 128
                            }
                        ]
                    }
                },
                {
                    "description": "RANDOM",
                    "boundingPoly": {
                        "vertices": [
                            {
                                "x": 105,
                                "y": 95
                            },
                            {
                                "x": 241,
                                "y": 95
                            },
                            {
                                "x": 241,
                                "y": 128
                            },
                            {
                                "x": 105,
                                "y": 128
                            }
                        ]
                    }
                },
                {
                    "description": "ASS",
                    "boundingPoly": {
                        "vertices": [
                            {
                                "x": 250,
                                "y": 95
                            },
                            {
                                "x": 316,
                                "y": 95
                            },
                            {
                                "x": 316,
                                "y": 128
                            },
                            {
                                "x": 250,
                                "y": 128
                            }
                        ]
                    }
                },
                {
                    "description": "COMMENT",
                    "boundingPoly": {
                        "vertices": [
                            {
                                "x": 322,
                                "y": 95
                            },
                            {
                                "x": 485,
                                "y": 95
                            },
                            {
                                "x": 485,
                                "y": 128
                            },
                            {
                                "x": 322,
                                "y": 128
                            }
                        ]
                    }
                },
                {
                    "description": "imgflip.com",
                    "boundingPoly": {
                        "vertices": [
                            {
                                "x": 3,
                                "y": 661
                            },
                            {
                                "x": 59,
                                "y": 662
                            },
                            {
                                "x": 59,
                                "y": 674
                            },
                            {
                                "x": 3,
                                "y": 673
                            }
                        ]
                    }
                }
            ],
            "fullTextAnnotation": {
                "pages": [
                    {
                        "property": {
                            "detectedLanguages": [
                                {
                                    "languageCode": "en",
                                    "confidence": 0.8177627
                                }
                            ]
                        },
                        "width": 500,
                        "height": 676,
                        "blocks": [
                            {
                                "boundingBox": {
                                    "vertices": [
                                        {
                                            "x": 6,
                                            "y": 8
                                        },
                                        {
                                            "x": 485,
                                            "y": 8
                                        },
                                        {
                                            "x": 485,
                                            "y": 128
                                        },
                                        {
                                            "x": 6,
                                            "y": 128
                                        }
                                    ]
                                },
                                "paragraphs": [
                                    {
                                        "boundingBox": {
                                            "vertices": [
                                                {
                                                    "x": 6,
                                                    "y": 8
                                                },
                                                {
                                                    "x": 485,
                                                    "y": 8
                                                },
                                                {
                                                    "x": 485,
                                                    "y": 128
                                                },
                                                {
                                                    "x": 6,
                                                    "y": 128
                                                }
                                            ]
                                        },
                                        "words": [
                                            {
                                                "property": {
                                                    "detectedLanguages": [
                                                        {
                                                            "languageCode": "en",
                                                            "confidence": 1
                                                        }
                                                    ]
                                                },
                                                "boundingBox": {
                                                    "vertices": [
                                                        {
                                                            "x": 77,
                                                            "y": 8
                                                        },
                                                        {
                                                            "x": 159,
                                                            "y": 8
                                                        },
                                                        {
                                                            "x": 159,
                                                            "y": 40
                                                        },
                                                        {
                                                            "x": 77,
                                                            "y": 40
                                                        }
                                                    ]
                                                },
                                                "symbols": [
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 77,
                                                                    "y": 8
                                                                },
                                                                {
                                                                    "x": 113,
                                                                    "y": 8
                                                                },
                                                                {
                                                                    "x": 113,
                                                                    "y": 40
                                                                },
                                                                {
                                                                    "x": 77,
                                                                    "y": 40
                                                                }
                                                            ]
                                                        },
                                                        "text": "W"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 109,
                                                                    "y": 8
                                                                },
                                                                {
                                                                    "x": 135,
                                                                    "y": 8
                                                                },
                                                                {
                                                                    "x": 135,
                                                                    "y": 40
                                                                },
                                                                {
                                                                    "x": 109,
                                                                    "y": 40
                                                                }
                                                            ]
                                                        },
                                                        "text": "H"
                                                    },
                                                    {
                                                        "property": {
                                                            "detectedBreak": {
                                                                "type": "SPACE"
                                                            }
                                                        },
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 135,
                                                                    "y": 8
                                                                },
                                                                {
                                                                    "x": 159,
                                                                    "y": 8
                                                                },
                                                                {
                                                                    "x": 159,
                                                                    "y": 40
                                                                },
                                                                {
                                                                    "x": 135,
                                                                    "y": 40
                                                                }
                                                            ]
                                                        },
                                                        "text": "O"
                                                    }
                                                ]
                                            },
                                            {
                                                "property": {
                                                    "detectedLanguages": [
                                                        {
                                                            "languageCode": "en",
                                                            "confidence": 1
                                                        }
                                                    ]
                                                },
                                                "boundingBox": {
                                                    "vertices": [
                                                        {
                                                            "x": 177,
                                                            "y": 8
                                                        },
                                                        {
                                                            "x": 230,
                                                            "y": 8
                                                        },
                                                        {
                                                            "x": 230,
                                                            "y": 40
                                                        },
                                                        {
                                                            "x": 177,
                                                            "y": 40
                                                        }
                                                    ]
                                                },
                                                "symbols": [
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 177,
                                                                    "y": 8
                                                                },
                                                                {
                                                                    "x": 201,
                                                                    "y": 8
                                                                },
                                                                {
                                                                    "x": 201,
                                                                    "y": 40
                                                                },
                                                                {
                                                                    "x": 177,
                                                                    "y": 40
                                                                }
                                                            ]
                                                        },
                                                        "text": "A"
                                                    },
                                                    {
                                                        "property": {
                                                            "detectedBreak": {
                                                                "type": "SPACE"
                                                            }
                                                        },
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 202,
                                                                    "y": 8
                                                                },
                                                                {
                                                                    "x": 230,
                                                                    "y": 8
                                                                },
                                                                {
                                                                    "x": 230,
                                                                    "y": 40
                                                                },
                                                                {
                                                                    "x": 202,
                                                                    "y": 40
                                                                }
                                                            ]
                                                        },
                                                        "text": "M"
                                                    }
                                                ]
                                            },
                                            {
                                                "property": {
                                                    "detectedLanguages": [
                                                        {
                                                            "languageCode": "en",
                                                            "confidence": 1
                                                        }
                                                    ]
                                                },
                                                "boundingBox": {
                                                    "vertices": [
                                                        {
                                                            "x": 253,
                                                            "y": 8
                                                        },
                                                        {
                                                            "x": 418,
                                                            "y": 8
                                                        },
                                                        {
                                                            "x": 418,
                                                            "y": 40
                                                        },
                                                        {
                                                            "x": 253,
                                                            "y": 40
                                                        }
                                                    ]
                                                },
                                                "symbols": [
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 253,
                                                                    "y": 8
                                                                },
                                                                {
                                                                    "x": 266,
                                                                    "y": 8
                                                                },
                                                                {
                                                                    "x": 266,
                                                                    "y": 40
                                                                },
                                                                {
                                                                    "x": 253,
                                                                    "y": 40
                                                                }
                                                            ]
                                                        },
                                                        "text": "I"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 272,
                                                                    "y": 8
                                                                },
                                                                {
                                                                    "x": 296,
                                                                    "y": 8
                                                                },
                                                                {
                                                                    "x": 296,
                                                                    "y": 40
                                                                },
                                                                {
                                                                    "x": 272,
                                                                    "y": 40
                                                                }
                                                            ]
                                                        },
                                                        "text": "C"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 295,
                                                                    "y": 8
                                                                },
                                                                {
                                                                    "x": 317,
                                                                    "y": 8
                                                                },
                                                                {
                                                                    "x": 317,
                                                                    "y": 40
                                                                },
                                                                {
                                                                    "x": 295,
                                                                    "y": 40
                                                                }
                                                            ]
                                                        },
                                                        "text": "O"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 317,
                                                                    "y": 8
                                                                },
                                                                {
                                                                    "x": 341,
                                                                    "y": 8
                                                                },
                                                                {
                                                                    "x": 341,
                                                                    "y": 40
                                                                },
                                                                {
                                                                    "x": 317,
                                                                    "y": 40
                                                                }
                                                            ]
                                                        },
                                                        "text": "O"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 338,
                                                                    "y": 8
                                                                },
                                                                {
                                                                    "x": 362,
                                                                    "y": 8
                                                                },
                                                                {
                                                                    "x": 362,
                                                                    "y": 40
                                                                },
                                                                {
                                                                    "x": 338,
                                                                    "y": 40
                                                                }
                                                            ]
                                                        },
                                                        "text": "K"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 360,
                                                                    "y": 8
                                                                },
                                                                {
                                                                    "x": 374,
                                                                    "y": 8
                                                                },
                                                                {
                                                                    "x": 374,
                                                                    "y": 40
                                                                },
                                                                {
                                                                    "x": 360,
                                                                    "y": 40
                                                                }
                                                            ]
                                                        },
                                                        "text": "I"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 374,
                                                                    "y": 8
                                                                },
                                                                {
                                                                    "x": 396,
                                                                    "y": 8
                                                                },
                                                                {
                                                                    "x": 396,
                                                                    "y": 40
                                                                },
                                                                {
                                                                    "x": 374,
                                                                    "y": 40
                                                                }
                                                            ]
                                                        },
                                                        "text": "N"
                                                    },
                                                    {
                                                        "property": {
                                                            "detectedBreak": {
                                                                "type": "EOL_SURE_SPACE"
                                                            }
                                                        },
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 395,
                                                                    "y": 8
                                                                },
                                                                {
                                                                    "x": 418,
                                                                    "y": 8
                                                                },
                                                                {
                                                                    "x": 418,
                                                                    "y": 40
                                                                },
                                                                {
                                                                    "x": 395,
                                                                    "y": 40
                                                                }
                                                            ]
                                                        },
                                                        "text": "G"
                                                    }
                                                ]
                                            },
                                            {
                                                "property": {
                                                    "detectedLanguages": [
                                                        {
                                                            "languageCode": "en",
                                                            "confidence": 1
                                                        }
                                                    ]
                                                },
                                                "boundingBox": {
                                                    "vertices": [
                                                        {
                                                            "x": 75,
                                                            "y": 52
                                                        },
                                                        {
                                                            "x": 149,
                                                            "y": 52
                                                        },
                                                        {
                                                            "x": 149,
                                                            "y": 86
                                                        },
                                                        {
                                                            "x": 75,
                                                            "y": 86
                                                        }
                                                    ]
                                                },
                                                "symbols": [
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 75,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 99,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 99,
                                                                    "y": 86
                                                                },
                                                                {
                                                                    "x": 75,
                                                                    "y": 86
                                                                }
                                                            ]
                                                        },
                                                        "text": "U"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 99,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 120,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 120,
                                                                    "y": 86
                                                                },
                                                                {
                                                                    "x": 99,
                                                                    "y": 86
                                                                }
                                                            ]
                                                        },
                                                        "text": "P"
                                                    },
                                                    {
                                                        "property": {
                                                            "detectedBreak": {
                                                                "type": "SPACE"
                                                            }
                                                        },
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 125,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 149,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 149,
                                                                    "y": 86
                                                                },
                                                                {
                                                                    "x": 125,
                                                                    "y": 86
                                                                }
                                                            ]
                                                        },
                                                        "text": "A"
                                                    }
                                                ]
                                            },
                                            {
                                                "property": {
                                                    "detectedLanguages": [
                                                        {
                                                            "languageCode": "en",
                                                            "confidence": 1
                                                        }
                                                    ]
                                                },
                                                "boundingBox": {
                                                    "vertices": [
                                                        {
                                                            "x": 155,
                                                            "y": 52
                                                        },
                                                        {
                                                            "x": 258,
                                                            "y": 52
                                                        },
                                                        {
                                                            "x": 258,
                                                            "y": 86
                                                        },
                                                        {
                                                            "x": 155,
                                                            "y": 86
                                                        }
                                                    ]
                                                },
                                                "symbols": [
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 155,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 172,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 172,
                                                                    "y": 86
                                                                },
                                                                {
                                                                    "x": 155,
                                                                    "y": 86
                                                                }
                                                            ]
                                                        },
                                                        "text": "F"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 171,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 193,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 193,
                                                                    "y": 86
                                                                },
                                                                {
                                                                    "x": 171,
                                                                    "y": 86
                                                                }
                                                            ]
                                                        },
                                                        "text": "U"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 192,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 213,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 213,
                                                                    "y": 86
                                                                },
                                                                {
                                                                    "x": 192,
                                                                    "y": 86
                                                                }
                                                            ]
                                                        },
                                                        "text": "N"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 215,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 235,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 235,
                                                                    "y": 86
                                                                },
                                                                {
                                                                    "x": 215,
                                                                    "y": 86
                                                                }
                                                            ]
                                                        },
                                                        "text": "N"
                                                    },
                                                    {
                                                        "property": {
                                                            "detectedBreak": {
                                                                "type": "SPACE"
                                                            }
                                                        },
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 237,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 258,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 258,
                                                                    "y": 86
                                                                },
                                                                {
                                                                    "x": 237,
                                                                    "y": 86
                                                                }
                                                            ]
                                                        },
                                                        "text": "Y"
                                                    }
                                                ]
                                            },
                                            {
                                                "property": {
                                                    "detectedLanguages": [
                                                        {
                                                            "languageCode": "en",
                                                            "confidence": 1
                                                        }
                                                    ]
                                                },
                                                "boundingBox": {
                                                    "vertices": [
                                                        {
                                                            "x": 263,
                                                            "y": 52
                                                        },
                                                        {
                                                            "x": 360,
                                                            "y": 52
                                                        },
                                                        {
                                                            "x": 360,
                                                            "y": 86
                                                        },
                                                        {
                                                            "x": 263,
                                                            "y": 86
                                                        }
                                                    ]
                                                },
                                                "symbols": [
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 263,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 284,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 284,
                                                                    "y": 86
                                                                },
                                                                {
                                                                    "x": 263,
                                                                    "y": 86
                                                                }
                                                            ]
                                                        },
                                                        "text": "R"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 286,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 302,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 302,
                                                                    "y": 86
                                                                },
                                                                {
                                                                    "x": 286,
                                                                    "y": 86
                                                                }
                                                            ]
                                                        },
                                                        "text": "E"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 302,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 324,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 324,
                                                                    "y": 86
                                                                },
                                                                {
                                                                    "x": 302,
                                                                    "y": 86
                                                                }
                                                            ]
                                                        },
                                                        "text": "P"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 322,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 342,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 342,
                                                                    "y": 86
                                                                },
                                                                {
                                                                    "x": 322,
                                                                    "y": 86
                                                                }
                                                            ]
                                                        },
                                                        "text": "L"
                                                    },
                                                    {
                                                        "property": {
                                                            "detectedBreak": {
                                                                "type": "SPACE"
                                                            }
                                                        },
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 337,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 360,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 360,
                                                                    "y": 86
                                                                },
                                                                {
                                                                    "x": 337,
                                                                    "y": 86
                                                                }
                                                            ]
                                                        },
                                                        "text": "Y"
                                                    }
                                                ]
                                            },
                                            {
                                                "property": {
                                                    "detectedLanguages": [
                                                        {
                                                            "languageCode": "en",
                                                            "confidence": 1
                                                        }
                                                    ]
                                                },
                                                "boundingBox": {
                                                    "vertices": [
                                                        {
                                                            "x": 362,
                                                            "y": 52
                                                        },
                                                        {
                                                            "x": 424,
                                                            "y": 52
                                                        },
                                                        {
                                                            "x": 424,
                                                            "y": 86
                                                        },
                                                        {
                                                            "x": 362,
                                                            "y": 86
                                                        }
                                                    ]
                                                },
                                                "symbols": [
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 362,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 382,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 382,
                                                                    "y": 86
                                                                },
                                                                {
                                                                    "x": 362,
                                                                    "y": 86
                                                                }
                                                            ]
                                                        },
                                                        "text": "F"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 378,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 403,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 403,
                                                                    "y": 86
                                                                },
                                                                {
                                                                    "x": 378,
                                                                    "y": 86
                                                                }
                                                            ]
                                                        },
                                                        "text": "O"
                                                    },
                                                    {
                                                        "property": {
                                                            "detectedBreak": {
                                                                "type": "EOL_SURE_SPACE"
                                                            }
                                                        },
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 401,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 424,
                                                                    "y": 52
                                                                },
                                                                {
                                                                    "x": 424,
                                                                    "y": 86
                                                                },
                                                                {
                                                                    "x": 401,
                                                                    "y": 86
                                                                }
                                                            ]
                                                        },
                                                        "text": "R"
                                                    }
                                                ]
                                            },
                                            {
                                                "property": {
                                                    "detectedLanguages": [
                                                        {
                                                            "languageCode": "en",
                                                            "confidence": 1
                                                        }
                                                    ]
                                                },
                                                "boundingBox": {
                                                    "vertices": [
                                                        {
                                                            "x": 6,
                                                            "y": 95
                                                        },
                                                        {
                                                            "x": 98,
                                                            "y": 95
                                                        },
                                                        {
                                                            "x": 98,
                                                            "y": 128
                                                        },
                                                        {
                                                            "x": 6,
                                                            "y": 128
                                                        }
                                                    ]
                                                },
                                                "symbols": [
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 6,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 28,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 28,
                                                                    "y": 128
                                                                },
                                                                {
                                                                    "x": 6,
                                                                    "y": 128
                                                                }
                                                            ]
                                                        },
                                                        "text": "S"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 29,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 51,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 51,
                                                                    "y": 128
                                                                },
                                                                {
                                                                    "x": 29,
                                                                    "y": 128
                                                                }
                                                            ]
                                                        },
                                                        "text": "O"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 52,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 78,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 78,
                                                                    "y": 128
                                                                },
                                                                {
                                                                    "x": 52,
                                                                    "y": 128
                                                                }
                                                            ]
                                                        },
                                                        "text": "M"
                                                    },
                                                    {
                                                        "property": {
                                                            "detectedBreak": {
                                                                "type": "SPACE"
                                                            }
                                                        },
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 80,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 98,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 98,
                                                                    "y": 128
                                                                },
                                                                {
                                                                    "x": 80,
                                                                    "y": 128
                                                                }
                                                            ]
                                                        },
                                                        "text": "E"
                                                    }
                                                ]
                                            },
                                            {
                                                "property": {
                                                    "detectedLanguages": [
                                                        {
                                                            "languageCode": "en",
                                                            "confidence": 1
                                                        }
                                                    ]
                                                },
                                                "boundingBox": {
                                                    "vertices": [
                                                        {
                                                            "x": 105,
                                                            "y": 95
                                                        },
                                                        {
                                                            "x": 241,
                                                            "y": 95
                                                        },
                                                        {
                                                            "x": 241,
                                                            "y": 128
                                                        },
                                                        {
                                                            "x": 105,
                                                            "y": 128
                                                        }
                                                    ]
                                                },
                                                "symbols": [
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 105,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 125,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 125,
                                                                    "y": 128
                                                                },
                                                                {
                                                                    "x": 105,
                                                                    "y": 128
                                                                }
                                                            ]
                                                        },
                                                        "text": "R"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 125,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 147,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 147,
                                                                    "y": 128
                                                                },
                                                                {
                                                                    "x": 125,
                                                                    "y": 128
                                                                }
                                                            ]
                                                        },
                                                        "text": "A"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 148,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 168,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 168,
                                                                    "y": 128
                                                                },
                                                                {
                                                                    "x": 148,
                                                                    "y": 128
                                                                }
                                                            ]
                                                        },
                                                        "text": "N"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 169,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 191,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 191,
                                                                    "y": 128
                                                                },
                                                                {
                                                                    "x": 169,
                                                                    "y": 128
                                                                }
                                                            ]
                                                        },
                                                        "text": "D"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 192,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 214,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 214,
                                                                    "y": 128
                                                                },
                                                                {
                                                                    "x": 192,
                                                                    "y": 128
                                                                }
                                                            ]
                                                        },
                                                        "text": "O"
                                                    },
                                                    {
                                                        "property": {
                                                            "detectedBreak": {
                                                                "type": "SPACE"
                                                            }
                                                        },
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 215,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 241,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 241,
                                                                    "y": 128
                                                                },
                                                                {
                                                                    "x": 215,
                                                                    "y": 128
                                                                }
                                                            ]
                                                        },
                                                        "text": "M"
                                                    }
                                                ]
                                            },
                                            {
                                                "property": {
                                                    "detectedLanguages": [
                                                        {
                                                            "languageCode": "en",
                                                            "confidence": 1
                                                        }
                                                    ]
                                                },
                                                "boundingBox": {
                                                    "vertices": [
                                                        {
                                                            "x": 250,
                                                            "y": 95
                                                        },
                                                        {
                                                            "x": 316,
                                                            "y": 95
                                                        },
                                                        {
                                                            "x": 316,
                                                            "y": 128
                                                        },
                                                        {
                                                            "x": 250,
                                                            "y": 128
                                                        }
                                                    ]
                                                },
                                                "symbols": [
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 250,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 272,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 272,
                                                                    "y": 128
                                                                },
                                                                {
                                                                    "x": 250,
                                                                    "y": 128
                                                                }
                                                            ]
                                                        },
                                                        "text": "A"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 272,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 292,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 292,
                                                                    "y": 128
                                                                },
                                                                {
                                                                    "x": 272,
                                                                    "y": 128
                                                                }
                                                            ]
                                                        },
                                                        "text": "S"
                                                    },
                                                    {
                                                        "property": {
                                                            "detectedBreak": {
                                                                "type": "SPACE"
                                                            }
                                                        },
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 294,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 316,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 316,
                                                                    "y": 128
                                                                },
                                                                {
                                                                    "x": 294,
                                                                    "y": 128
                                                                }
                                                            ]
                                                        },
                                                        "text": "S"
                                                    }
                                                ]
                                            },
                                            {
                                                "property": {
                                                    "detectedLanguages": [
                                                        {
                                                            "languageCode": "en",
                                                            "confidence": 1
                                                        }
                                                    ]
                                                },
                                                "boundingBox": {
                                                    "vertices": [
                                                        {
                                                            "x": 322,
                                                            "y": 95
                                                        },
                                                        {
                                                            "x": 485,
                                                            "y": 95
                                                        },
                                                        {
                                                            "x": 485,
                                                            "y": 128
                                                        },
                                                        {
                                                            "x": 322,
                                                            "y": 128
                                                        }
                                                    ]
                                                },
                                                "symbols": [
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 322,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 345,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 345,
                                                                    "y": 128
                                                                },
                                                                {
                                                                    "x": 322,
                                                                    "y": 128
                                                                }
                                                            ]
                                                        },
                                                        "text": "C"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 343,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 366,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 366,
                                                                    "y": 128
                                                                },
                                                                {
                                                                    "x": 343,
                                                                    "y": 128
                                                                }
                                                            ]
                                                        },
                                                        "text": "O"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 368,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 395,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 395,
                                                                    "y": 128
                                                                },
                                                                {
                                                                    "x": 368,
                                                                    "y": 128
                                                                }
                                                            ]
                                                        },
                                                        "text": "M"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 395,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 422,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 422,
                                                                    "y": 128
                                                                },
                                                                {
                                                                    "x": 395,
                                                                    "y": 128
                                                                }
                                                            ]
                                                        },
                                                        "text": "M"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 424,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 444,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 444,
                                                                    "y": 128
                                                                },
                                                                {
                                                                    "x": 424,
                                                                    "y": 128
                                                                }
                                                            ]
                                                        },
                                                        "text": "E"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 441,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 462,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 462,
                                                                    "y": 128
                                                                },
                                                                {
                                                                    "x": 441,
                                                                    "y": 128
                                                                }
                                                            ]
                                                        },
                                                        "text": "N"
                                                    },
                                                    {
                                                        "property": {
                                                            "detectedBreak": {
                                                                "type": "LINE_BREAK"
                                                            }
                                                        },
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 464,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 485,
                                                                    "y": 95
                                                                },
                                                                {
                                                                    "x": 485,
                                                                    "y": 128
                                                                },
                                                                {
                                                                    "x": 464,
                                                                    "y": 128
                                                                }
                                                            ]
                                                        },
                                                        "text": "T"
                                                    }
                                                ]
                                            }
                                        ]
                                    }
                                ],
                                "blockType": "TEXT"
                            },
                            {
                                "boundingBox": {
                                    "vertices": [
                                        {
                                            "x": 3,
                                            "y": 661
                                        },
                                        {
                                            "x": 59,
                                            "y": 662
                                        },
                                        {
                                            "x": 59,
                                            "y": 674
                                        },
                                        {
                                            "x": 3,
                                            "y": 673
                                        }
                                    ]
                                },
                                "paragraphs": [
                                    {
                                        "boundingBox": {
                                            "vertices": [
                                                {
                                                    "x": 3,
                                                    "y": 661
                                                },
                                                {
                                                    "x": 59,
                                                    "y": 662
                                                },
                                                {
                                                    "x": 59,
                                                    "y": 674
                                                },
                                                {
                                                    "x": 3,
                                                    "y": 673
                                                }
                                            ]
                                        },
                                        "words": [
                                            {
                                                "boundingBox": {
                                                    "vertices": [
                                                        {
                                                            "x": 3,
                                                            "y": 661
                                                        },
                                                        {
                                                            "x": 59,
                                                            "y": 662
                                                        },
                                                        {
                                                            "x": 59,
                                                            "y": 674
                                                        },
                                                        {
                                                            "x": 3,
                                                            "y": 673
                                                        }
                                                    ]
                                                },
                                                "symbols": [
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 3,
                                                                    "y": 662
                                                                },
                                                                {
                                                                    "x": 7,
                                                                    "y": 662
                                                                },
                                                                {
                                                                    "x": 7,
                                                                    "y": 673
                                                                },
                                                                {
                                                                    "x": 3,
                                                                    "y": 673
                                                                }
                                                            ]
                                                        },
                                                        "text": "i"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 6,
                                                                    "y": 662
                                                                },
                                                                {
                                                                    "x": 15,
                                                                    "y": 662
                                                                },
                                                                {
                                                                    "x": 15,
                                                                    "y": 673
                                                                },
                                                                {
                                                                    "x": 6,
                                                                    "y": 673
                                                                }
                                                            ]
                                                        },
                                                        "text": "m"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 14,
                                                                    "y": 662
                                                                },
                                                                {
                                                                    "x": 21,
                                                                    "y": 662
                                                                },
                                                                {
                                                                    "x": 21,
                                                                    "y": 673
                                                                },
                                                                {
                                                                    "x": 14,
                                                                    "y": 673
                                                                }
                                                            ]
                                                        },
                                                        "text": "g"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 20,
                                                                    "y": 662
                                                                },
                                                                {
                                                                    "x": 24,
                                                                    "y": 662
                                                                },
                                                                {
                                                                    "x": 24,
                                                                    "y": 673
                                                                },
                                                                {
                                                                    "x": 20,
                                                                    "y": 673
                                                                }
                                                            ]
                                                        },
                                                        "text": "f"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 25,
                                                                    "y": 662
                                                                },
                                                                {
                                                                    "x": 28,
                                                                    "y": 662
                                                                },
                                                                {
                                                                    "x": 28,
                                                                    "y": 673
                                                                },
                                                                {
                                                                    "x": 25,
                                                                    "y": 673
                                                                }
                                                            ]
                                                        },
                                                        "text": "l"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 27,
                                                                    "y": 662
                                                                },
                                                                {
                                                                    "x": 30,
                                                                    "y": 662
                                                                },
                                                                {
                                                                    "x": 30,
                                                                    "y": 673
                                                                },
                                                                {
                                                                    "x": 27,
                                                                    "y": 673
                                                                }
                                                            ]
                                                        },
                                                        "text": "i"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 30,
                                                                    "y": 662
                                                                },
                                                                {
                                                                    "x": 37,
                                                                    "y": 662
                                                                },
                                                                {
                                                                    "x": 37,
                                                                    "y": 673
                                                                },
                                                                {
                                                                    "x": 30,
                                                                    "y": 673
                                                                }
                                                            ]
                                                        },
                                                        "text": "p"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 35,
                                                                    "y": 662
                                                                },
                                                                {
                                                                    "x": 40,
                                                                    "y": 662
                                                                },
                                                                {
                                                                    "x": 40,
                                                                    "y": 673
                                                                },
                                                                {
                                                                    "x": 35,
                                                                    "y": 673
                                                                }
                                                            ]
                                                        },
                                                        "text": "."
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 38,
                                                                    "y": 662
                                                                },
                                                                {
                                                                    "x": 46,
                                                                    "y": 662
                                                                },
                                                                {
                                                                    "x": 46,
                                                                    "y": 673
                                                                },
                                                                {
                                                                    "x": 38,
                                                                    "y": 673
                                                                }
                                                            ]
                                                        },
                                                        "text": "c"
                                                    },
                                                    {
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 44,
                                                                    "y": 662
                                                                },
                                                                {
                                                                    "x": 51,
                                                                    "y": 662
                                                                },
                                                                {
                                                                    "x": 51,
                                                                    "y": 673
                                                                },
                                                                {
                                                                    "x": 44,
                                                                    "y": 673
                                                                }
                                                            ]
                                                        },
                                                        "text": "o"
                                                    },
                                                    {
                                                        "property": {
                                                            "detectedBreak": {
                                                                "type": "LINE_BREAK"
                                                            }
                                                        },
                                                        "boundingBox": {
                                                            "vertices": [
                                                                {
                                                                    "x": 50,
                                                                    "y": 662
                                                                },
                                                                {
                                                                    "x": 59,
                                                                    "y": 662
                                                                },
                                                                {
                                                                    "x": 59,
                                                                    "y": 673
                                                                },
                                                                {
                                                                    "x": 50,
                                                                    "y": 673
                                                                }
                                                            ]
                                                        },
                                                        "text": "m"
                                                    }
                                                ]
                                            }
                                        ]
                                    }
                                ],
                                "blockType": "TEXT"
                            }
                        ]
                    }
                ],
                "text": "WHO AM ICOOKING\nUPA FUNNY REPLY FOR\nSOME RANDOM ASS COMMENT\nimgflip.com"
            }
        }
    ]
}


image_url = 'https://i.imgflip.com/9pfg17.jpg'

# convert the google api response to a list of bounding boxes
# that we can use to draw on the image using opencv
bounding_boxes = []
for annotation in google_api_response["responses"][0]["textAnnotations"]:
    vertices = annotation["boundingPoly"]["vertices"]
    # Skip if any vertex is missing coordinates
    if not all("x" in v and "y" in v for v in vertices):
        continue
    bounding_boxes.append({
        "x": vertices[0]["x"],
        "y": vertices[0]["y"],
        "width": vertices[1]["x"] - vertices[0]["x"],
        "height": vertices[2]["y"] - vertices[0]["y"]
    })
print(bounding_boxes)

# download the image and load into opencv
resp = httpx.get(image_url)
resp.raise_for_status()
image = cv2.imdecode(np.frombuffer(
    resp.content, np.uint8), cv2.IMREAD_COLOR)

# draw the bounding boxes on the image
for box in bounding_boxes:
    cv2.rectangle(image, (box["x"], box["y"]), (box["x"] +
                                                box["width"], box["y"] + box["height"]), (0, 0, 255), 2)

cv2.imwrite("image_with_bounding_boxes.jpg", image)
