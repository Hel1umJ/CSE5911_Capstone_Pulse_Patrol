import React from 'react';
import { render, screen } from '@testing-library/react';
import SmallSensorCard from './SmallSensorCard';

describe('SmallSensorCardHeartRate', () => {
  test('renders with default placeholder values', () => {
    render(<SmallSensorCard  
      iconName={"heart-pulse"}
      title={"Heart Rate"}
      path={"/heart_rate_val"}
      unit={"bpm"}/>);

    expect(screen.getByText(/Heart Rate/i)).toBeInTheDocument();
    expect(screen.getByText(/BPM/i)).toBeInTheDocument();

  });
});

describe('SmallSensorCardSPO2', () => {
  test('renders with default placeholder values', () => {
    render(<SmallSensorCard  
      iconName={"percent"}
      title={"SpO₂"}
      path={"/sp02_val"}
      unit={"%"}
      />);
    expect(screen.getByText(/SpO₂/i)).toBeInTheDocument();
    expect(screen.getByText(/%/i)).toBeInTheDocument();

  });
});