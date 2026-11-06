import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import Alerts from "@/pages/Alerts";
import type { ReactNode } from "react";

vi.mock("@/components/layout/AppLayout", () => ({ default: ({ children }: { children: ReactNode }) => <div>{children}</div> }));
vi.mock("@/api/price", () => ({ fetchAlertChannels: vi.fn().mockResolvedValue([]) }));
const quoteStore = vi.hoisted(() => ({ goldPrice: null as null | { data_type: string; real_time_price: number }, silverPrice: null as null | { data_type: string; real_time_price: number } }));
vi.mock("@/stores/priceStore", () => ({ default: () => quoteStore }));

class FakeEventSource extends EventTarget {
  static OPEN = 1;
  static instances: FakeEventSource[] = [];
  readyState = 1;
  onopen: (() => void) | null = null;
  onerror: (() => void) | null = null;
  constructor(public url: string) { super(); FakeEventSource.instances.push(this); }
  close() { this.readyState = 2; }
}

beforeEach(() => {
  FakeEventSource.instances = [];
  quoteStore.goldPrice = null;
  quoteStore.silverPrice = null;
  vi.stubGlobal("EventSource", FakeEventSource);
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.useRealTimers(); });

async function subscribe(metal: "gold" | "silver" = "gold") {
  await act(async () => { render(<Alerts />); });
  if (metal === "silver") fireEvent.click(screen.getByRole("button", { name: "🥈 白银" }));
  fireEvent.change(screen.getByRole("spinbutton"), { target: { value: "600" } });
  fireEvent.click(screen.getByRole("button", { name: "开始订阅" }));
  return FakeEventSource.instances[0];
}

it.each([["gold", "黄 金"], ["silver", "白 银"]] as const)("subscribes to the domestic %s data type for yuan-per-gram alerts", async (metal, dataType) => {
  const source = await subscribe(metal);
  expect(new URL(source.url, "http://localhost").searchParams.get("data_type")).toBe(dataType);
});

it("displays the backend price event payload", async () => {
  const source = await subscribe();
  act(() => { source.dispatchEvent(new MessageEvent("price", { data: JSON.stringify({ price: 601 }) })); });
  expect(screen.getByText("¥601.00")).toBeInTheDocument();
});

it("preserves the selected metal and greater-than direction from backend alert events", async () => {
  const source = await subscribe();
  act(() => { source.dispatchEvent(new MessageEvent("alert", { data: JSON.stringify({ price: 601, target: 600, op: "gte" }) })); });
  expect(screen.getByText("提醒触发：黄金 ≥ 600")).toBeInTheDocument();
});

it("keeps active stream context when controls change and ignores retired stream events", async () => {
  const first = await subscribe();
  fireEvent.click(screen.getByRole("button", { name: "🥈 白银" }));
  act(() => { first.dispatchEvent(new MessageEvent("price", { data: JSON.stringify({ price: 601 }) })); });
  expect(screen.getByText("¥601.00")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "开始订阅" }));
  const second = FakeEventSource.instances[1];
  expect(first.readyState).toBe(2);
  act(() => {
    first.dispatchEvent(new MessageEvent("price", { data: JSON.stringify({ price: 999 }) }));
    first.dispatchEvent(new MessageEvent("alert", { data: JSON.stringify({ price: 999, target: 999, op: "lte" }) }));
    second.dispatchEvent(new MessageEvent("price", { data: JSON.stringify({ price: 6.5 }) }));
    second.dispatchEvent(new MessageEvent("alert", { data: JSON.stringify({ price: 6.5, target: 7, op: "lte" }) }));
  });
  expect(screen.getByText("¥601.00")).toBeInTheDocument();
  expect(screen.getByText("¥6.50")).toBeInTheDocument();
  expect(screen.queryByText(/999/)).not.toBeInTheDocument();
  expect(screen.getByText("提醒触发：白银 ≤ 7")).toBeInTheDocument();
});

it("does not let a retired reconnect timer replace a new subscription", async () => {
  vi.useFakeTimers();
  const first = await subscribe();
  act(() => {
    first.dispatchEvent(new Event("error"));
    first.dispatchEvent(new Event("error"));
  });
  fireEvent.click(screen.getByRole("button", { name: "🥈 白银" }));
  fireEvent.click(screen.getByRole("button", { name: "开始订阅" }));
  act(() => { vi.advanceTimersByTime(5000); });
  expect(FakeEventSource.instances).toHaveLength(2);
  expect(new URL(FakeEventSource.instances[1].url, "http://localhost").searchParams.get("data_type")).toBe("白 银");
});

it("adapts backend payloads after reconnect and closes the current stream on unmount", async () => {
  vi.useFakeTimers();
  const first = await subscribe();
  act(() => { first.dispatchEvent(new Event("error")); vi.advanceTimersByTime(5000); });
  const second = FakeEventSource.instances[1];
  act(() => {
    second.dispatchEvent(new MessageEvent("price", { data: JSON.stringify({ price: 602 }) }));
    second.dispatchEvent(new MessageEvent("alert", { data: JSON.stringify({ price: 602, target: 600, op: "gte" }) }));
  });
  expect(screen.getByText("¥602.00")).toBeInTheDocument();
  expect(screen.getByText("提醒触发：黄金 ≥ 600")).toBeInTheDocument();
  cleanup();
  expect(second.readyState).toBe(2);
});

it("does not present international spot quotes as domestic yuan-per-gram prices", async () => {
  quoteStore.goldPrice = { data_type: "XAU", real_time_price: 2300 };
  quoteStore.silverPrice = { data_type: "XAG", real_time_price: 30 };
  await act(async () => { render(<Alerts />); });
  expect(screen.queryByText("¥2300.00")).not.toBeInTheDocument();
  expect(screen.queryByText("¥30.00")).not.toBeInTheDocument();
});
