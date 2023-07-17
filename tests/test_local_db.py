import unittest, configparser, os
from src.db.tables import Violator, ViolationDetails, DeviceDetails
from src.db.crud import DatabaseCRUD
from sqlalchemy import func
from faker import Faker
from csv import DictWriter
import time

CONFIG_FILE = "./cfg/app.cfg"
DB_FILE = "data/test_db.sqlite"

# Test the Configuration File Contents
class TestConfigFiles(unittest.TestCase):

    def setUp(self):
        self.configparser = configparser.ConfigParser()
        self.configparser.read(CONFIG_FILE)

    def test_step_2_yolor_filepaths(self):
        options = [
            "classes",
            "cfg"
        ]
        for option in options:
            filepath = self.configparser.get("yolor", option)
            self.assertTrue(os.path.exists(filepath), f"{filepath} file does not exist.")

    def test_step_3_device(self):
        device = self.configparser.get("yolor", "device")
        self.assertEqual(device, "cpu")

# Test Local Database CRUD Functions
class TestDatabaseCRUD(unittest.TestCase):

    violators = []
    cfg = configparser.ConfigParser()
    db = DatabaseCRUD(db_URL=f"sqlite:///{DB_FILE}")
    faker = Faker()

    def setUp(self):
        self.cfg.read(CONFIG_FILE)

    @classmethod
    def tearDownClass(cls):
        cls.db.session.close()
        cls.db.engine.dispose()
        os.remove(DB_FILE)

    def test_step_1_load_data(self):
        self.db.insertPPEClasses(self.cfg.get("yolor", "classes"))
        ppe_classes = self.db.getPPEClasses()
        self.assertGreater(len(ppe_classes), 0)

    def test_step_2_insert_violation_details_with_violators(self):

        devicedetails = DeviceDetails()
        self.db.session.add(devicedetails)
        self.db.session.flush()
        devicedetails_id = devicedetails.id
        self.db.session.commit()
        self.db.session.close()

        # Create violation details
        violationdetails = ViolationDetails()
        self.db.session.add(violationdetails)
        self.db.session.flush()
        violationdetails_id = violationdetails.id
        self.db.session.commit()
        self.db.session.close()

        result = self.db.insertViolationDetailsToDeviceDetails(devicedetails_id, violationdetails_id)
        self.assertTrue(result)

        # Insert violator entry with the correct inputs
        detected = [
                {"id": 1, "class_name": "no helmet", "confidence": 0.75, "overlaps": [1, 2]}, 
                {"id": 2, "class_name": "no glasses", "confidence": 0.80, "overlaps": [1,]}, 
                {"id": 3, "class_name": "no gloves", "confidence": 0.76, "overlaps": [1,]}, 
                {"id": 4, "class_name": "no boots", "confidence": 0.9, "overlaps": [1,]}
        ]
        result = self.db.insertViolator(
                violationdetails_id=violationdetails_id, 
                bbox_id=1, 
                topleft=(0, 0), 
                bottomright=(100, 400), 
                detectedppe=detected
        )
        self.assertTrue(result)

        # Insert violator entry with the same name (NOTE: This case is possible when there are multiple recognized faces)
        detected = [
                {"id": 5, "class_name": "no helmet", "confidence": 0.75, "overlaps": [1, 2]}, 
                {"id": 6, "class_name": "no glasses", "confidence": 0.98, "overlaps": [2,]}, 
                {"id": 7, "class_name": "no gloves", "confidence": 0.91, "overlaps": [2,]}, 
                {"id": 8, "class_name": "no boots", "confidence": 0.90, "overlaps": [2,]}
        ]
        result = self.db.insertViolator(
                violationdetails_id=violationdetails_id, 
                bbox_id=2,
                topleft=(0, 0), 
                bottomright=(100, 400), 
                detectedppe=detected
        )
        self.assertTrue(result)

        # # Check the number of rows in the Violator. The result should be 2, because insertion is performed twice
        count = self.db.session.query(func.count(Violator.id)).scalar()
        self.assertEqual(count, 2)

        # Insert violator entry with non existing ppe classes
        detected = [
                {"id": 9, "class_name": "no helmet", "confidence": 0.62, "overlaps": [3,]}, 
                {"id": 10, "class_name": "pencil", "confidence": 0.95, "overlaps": [3,]}, 
                {"id": 11, "class_name": "cap", "confidence": 0.92, "overlaps": [3,]}
        ]
        result = self.db.insertViolator(
                violationdetails_id=violationdetails_id, 
                bbox_id=3,
                topleft=(0, 0), 
                bottomright=(100, 400), 
                detectedppe=detected
        )
        self.assertFalse(result)

    def test_step_5_delete_violator(self):
        # Delete violator with correct inputs
        result = self.db.deleteViolator("1")
        self.assertTrue(result)

        result = self.db.deleteViolator("2")
        self.assertTrue(result)

        # Delete the same violator once again
        result = self.db.deleteViolator("2")
        self.assertFalse(result)

        count = self.db.session.query(func.count(Violator.id)).scalar()
        self.assertEqual(count, 0)

    def test_step_6_update_device_details_status(self):
        result = self.db.setDeviceDetailsStatus("doesnotexist", False)
        self.assertFalse(result)

if __name__=="__main__":
    unittest.main()
