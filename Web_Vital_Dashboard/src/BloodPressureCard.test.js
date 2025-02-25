import React from 'react';
import { render, screen } from '@testing-library/react';
import BloodPressureCard from './BloodPressureCard';

describe('BloodPressureCard', () => {
  test('renders with default placeholder values', () => {
    render(<BloodPressureCard />);

    // Check for the heading
    expect(screen.getByText(/Blood Pressure/i)).toBeInTheDocument();

    // Check for the SYS and DIA labels
    expect(screen.getByText(/SYS/i)).toBeInTheDocument();
    expect(screen.getByText(/DIA/i)).toBeInTheDocument();
  });
});
