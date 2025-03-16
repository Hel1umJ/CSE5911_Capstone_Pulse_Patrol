const mockSocket = {
    on: jest.fn(),
    emit: jest.fn(),
    disconnect: jest.fn()
  };
  
  jest.mock("socket.io-client", () => ({
    io: () => mockSocket
  }));
  
  jest.mock("axios", () => ({
    get: jest.fn()
  }));
  
  import React from "react";
  import { render, screen, fireEvent, waitFor } from "@testing-library/react";
  import FlowRateCard from "./FlowRateCard";
  import axios from "axios";
  import { io } from "socket.io-client";
  
  describe("FlowRateCard", () => {
    beforeEach(() => {
      axios.get.mockResolvedValue({ data: { flow_rate: 5 } });
    });
  
    afterEach(() => {
      jest.clearAllMocks();
    });
  
    test("renders header and unit", () => {
      render(<FlowRateCard />);
      expect(screen.getByText(/Flow Rate Control/i)).toBeInTheDocument();
      expect(screen.getByText(/mL\/min/i)).toBeInTheDocument();
    });
  
    test("displays fetched initial flow rate", async () => {
      render(<FlowRateCard />);
      await waitFor(() => expect(screen.getByText("5")).toBeInTheDocument());
    });
  
    test("shows + and − buttons when socket connects", async () => {
      render(<FlowRateCard />);
      const connectCallback = mockSocket.on.mock.calls.find(([event]) => event === "connect")[1];
      connectCallback();
  
      await waitFor(() => {
        expect(screen.getByText("+")).toBeInTheDocument();
        expect(screen.getByText("−")).toBeInTheDocument();
      });
    });
  
    test("clicking + increases flow rate and emits update", async () => {
      render(<FlowRateCard />);
      const connectCallback = mockSocket.on.mock.calls.find(([event]) => event === "connect")[1];
      connectCallback();
      await waitFor(() => screen.getByText("5"));
  
      fireEvent.click(screen.getByText("+"));
      expect(screen.getByText("6")).toBeInTheDocument();
      expect(mockSocket.emit).toHaveBeenCalledWith("update_flow_rate", { flow_rate: 6 });
    });
  
    test("clicking − decreases flow rate and emits update", async () => {
      render(<FlowRateCard />);
      const connectCallback = mockSocket.on.mock.calls.find(([event]) => event === "connect")[1];
      connectCallback();
      await waitFor(() => screen.getByText("5"));
  
      fireEvent.click(screen.getByText("−"));
      expect(screen.getByText("4")).toBeInTheDocument();
      expect(mockSocket.emit).toHaveBeenCalledWith("update_flow_rate", { flow_rate: 4 });
    });
  
    test("flow rate does not exceed 30", async () => {
      axios.get.mockResolvedValue({ data: { flow_rate: 30 } });
      render(<FlowRateCard />);
      const connectCallback = mockSocket.on.mock.calls.find(([event]) => event === "connect")[1];
      connectCallback();
      await waitFor(() => screen.getByText("30"));
  
      fireEvent.click(screen.getByText("+"));
      expect(screen.getByText("30")).toBeInTheDocument(); 
    });
  
    test("flow rate does not go below 0", async () => {
      axios.get.mockResolvedValue({ data: { flow_rate: 0 } });
      render(<FlowRateCard />);
      const connectCallback = mockSocket.on.mock.calls.find(([event]) => event === "connect")[1];
      connectCallback();
      await waitFor(() => screen.getByText("0"));
  
      fireEvent.click(screen.getByText("−"));
      expect(screen.getByText("0")).toBeInTheDocument();
    });
  });
  