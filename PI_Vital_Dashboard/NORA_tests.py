import unittest
import tkinter as tk
from tkinter import ttk
from unittest.mock import patch, MagicMock
import NORA

# To run type: python -m unittest NORA_tests.py

class NORA_tests(unittest.TestCase):

    def setUp(self):
        self.root = NORA.create_gui()

    def tearDown(self):
        self.root.destroy()

    # The first 8 tests make sure each frame is created and all
    # the text is correct

    def test_window_exists(self):
        self.assertTrue(isinstance(self.root, tk.Tk))

    def test_main_frame_exists(self):
        main_frame = self.root.winfo_children()[0]
        self.assertTrue(isinstance(main_frame, ttk.Frame))

    def test_header_frame_exists(self):
        main_frame = self.root.winfo_children()[0]
        header_frame = main_frame.winfo_children()[0]
        self.assertTrue(isinstance(header_frame, ttk.Frame))
        header_label = header_frame.winfo_children()[1].winfo_children()[0]
        self.assertEqual(header_label.cget("text"), "NORA Vitals Monitor")

    def test_patient_info_frame_exists(self):
        main_frame = self.root.winfo_children()[0]
        patient_frame = main_frame.winfo_children()[1]
        self.assertTrue(isinstance(patient_frame, ttk.Frame))
        patient_title = patient_frame.winfo_children()[0]
        self.assertEqual(patient_title.cget("text"), "Patient Information")

    def test_flow_rate_frame_exists(self):
        main_frame = self.root.winfo_children()[0]
        flow_frame = main_frame.winfo_children()[2]
        self.assertTrue(isinstance(flow_frame, ttk.Frame))
        flow_title = flow_frame.winfo_children()[0]
        self.assertEqual(flow_title.cget("text"), "Flow Rate Control")

    def test_vitals_frame_exists(self):
        main_frame = self.root.winfo_children()[0]
        vitals_frame = main_frame.winfo_children()[3]
        self.assertTrue(isinstance(vitals_frame, ttk.Frame))

    def test_ecg_graph_frame_exists(self):
        main_frame = self.root.winfo_children()[0]
        graph_frame = main_frame.winfo_children()[4]
        self.assertTrue(isinstance(graph_frame, ttk.Frame))
        graph_title = graph_frame.winfo_children()[0]
        self.assertEqual(graph_title.cget("text"), "ECG Monitoring")

    def test_footer_frame_exists(self):
        main_frame = self.root.winfo_children()[0]
        footer_frame = main_frame.winfo_children()[5]
        self.assertTrue(isinstance(footer_frame, tk.Frame))
        footer_label = footer_frame.winfo_children()[0]
        self.assertEqual(footer_label.cget("text"), "NORA Vitals Monitor v2.0 | OSU Pulse Patrol")

    # The following 2 tests make sure the buttons in the change flow rate frame work

    @patch('NORA.requests.post')
    def test_flow_rate_increase_button(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.json.return_value = {"timestamp": 1234567891.0, "flow_rate": 5.5}
        initial_flow = NORA.flow_rate
        flow_frame = self.root.winfo_children()[0].winfo_children()[2]
        increase_button = flow_frame.winfo_children()[1].winfo_children()[1].winfo_children()[1]
        increase_button.invoke()
        self.assertEqual(NORA.flow_rate, initial_flow + 0.5)

    @patch('NORA.requests.post')
    def test_flow_rate_decrease_button(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.json.return_value = {"timestamp": 1234567891.0, "flow_rate": 5.5}
        initial_flow = NORA.flow_rate
        flow_frame = self.root.winfo_children()[0].winfo_children()[2]
        decrease_button = flow_frame.winfo_children()[1].winfo_children()[1].winfo_children()[0]
        decrease_button.invoke()
        self.assertEqual(NORA.flow_rate, initial_flow - 0.5)

    # The next 3 tests make sure that value updates work for heart rate, SpO2 change,
    # and blood pressure work

    @patch('NORA.requests.post')
    @patch('NORA.rand.randint')
    def test_hr_change(self, mock_randint, mock_post):
        mock_randint.side_effect = [80, 99, 120, 80]  # hr, spo2, bp_sys, bp_dia
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.json.return_value = {}

        NORA.update_vitals(self.root)
        hr_label = NORA.vital_labels["hr"]
        self.assertEqual(hr_label.cget("text"), "80 bpm")

        mock_randint.side_effect = [90, 99, 120, 80]
        NORA.update_vitals(self.root)
        self.assertEqual(hr_label.cget("text"), "90 bpm")

        # Ensure no unexpected HTTP request was made
        mock_post.assert_called()  


    @patch('NORA.requests.post')
    @patch('NORA.rand.randint')
    def test_spo2_change(self, mock_randint, mock_post):
        mock_randint.side_effect = [80, 99, 120, 80]
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.json.return_value = {}

        NORA.update_vitals(self.root)
        spo2_label = NORA.vital_labels["spo2"]
        self.assertEqual(spo2_label.cget("text"), "99%")

        mock_randint.side_effect = [80, 95, 120, 80]
        NORA.update_vitals(self.root)
        self.assertEqual(spo2_label.cget("text"), "95%")

        mock_post.assert_called()

    @patch('NORA.requests.post')
    @patch('NORA.rand.randint')
    def test_bp_change(self, mock_randint, mock_post):
        mock_randint.side_effect = [80, 99, 120, 80]
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.json.return_value = {}

        NORA.update_vitals(self.root)
        bp_label = NORA.vital_labels["bp"]
        self.assertEqual(bp_label.cget("text"), "120/80 mmHg")

        mock_randint.side_effect = [80, 99, 130, 90]
        NORA.update_vitals(self.root)
        self.assertEqual(bp_label.cget("text"), "130/90 mmHg")

        mock_post.assert_called()
