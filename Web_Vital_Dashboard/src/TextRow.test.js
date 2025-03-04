import React from 'react';
import { render, screen } from '@testing-library/react';
import TextRow from './TextRow';

describe('HeartRateCard', () => {
    test('renders with default placeholder values', () => {
      render(<TextRow title={"Heart Rate"} subtitle={"BPM"}/>);
  
      // Check for the heading
      expect(screen.getByText(/Heart Rate/i)).toBeInTheDocument();
      expect(screen.getByText(/BPM/i)).toBeInTheDocument();
    });
  });

  describe('SPO2Card', () => {
    test('renders with default placeholder values', () => {
      render(<TextRow title={"SP02"} subtitle={"%"}/>);
  
      // Check for the heading
      expect(screen.getByText(/SP02/i)).toBeInTheDocument();
      expect(screen.getByText(/%/i)).toBeInTheDocument();
    });
  });