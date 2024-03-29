try:
    import unittest, configparser, cv2, os
    from yolor.utils.datasets import letterbox
    from src.detection import Detection
    import numpy as np

    CONFIG_FILE = "./cfg/app.cfg"
    configparser = configparser.ConfigParser()
    configparser.read(CONFIG_FILE)
    detection = Detection(configparser)
    base_path_test_images = "data/samples/images/tests"

    def processImage(image: np.ndarray) -> np.ndarray:
        """
        Add an additional dimension to the image and convert it from BGR to RGB format. This function will be used in the detection model.
        """
        img: np.ndarray = image.copy()
        img = img[:,:,::-1]
        img = letterbox(img, new_shape=(640, 640), auto=True)[0]
        img = np.expand_dims(img, axis=0)
        img = img.transpose(0, 3, 1, 2)
        return img

    @unittest.skip
    class TestDetect(unittest.TestCase):

        """
        Methods:
            - setUp                                 ()
            - test_step_1_detect_one_violator       ()
            - test_step_2_detect_no_violator        ()
            - test_step_3_detect_many_violators     ()
        """

        def test_step_1_detect_one_violator(self):
            path = os.path.join(base_path_test_images, "frame_19947.jpg")
            img = cv2.imread(path)
            processed_img = processImage(img)
            persons, ppe = detection.detect(processed_img, img)
            self.assertEqual(len(persons), 1)
        
        def test_step_2_detect_no_violator(self):
            path = os.path.join(base_path_test_images, "frame_732.jpg")
            img = cv2.imread(path)
            processed_img = processImage(img)
            persons, ppe = detection.detect(processed_img, img)
            self.assertEqual(len(persons), 0)

except Exception as e:
    print(f"{e}")

