import React from 'react';
import { render, screen } from '@testing-library/react';
import AccentCard from './AccentCard';

describe('AccentCard', () => {
  test('renders with default placeholder values', () => {
    render(<AccentCard />);

    expect(screen.getByText(/#/i)).toBeInTheDocument();
    expect(screen.getByText(/DOB/i)).toBeInTheDocument();

    expect(screen.getByText(/Heart Rate/i)).toBeInTheDocument();
    expect(screen.getByText(/SpO₂/i)).toBeInTheDocument();

  });
});
