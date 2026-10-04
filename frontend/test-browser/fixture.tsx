// Browser-only engineering fixture; not an entry in the production build.
import { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import { useRecommendations } from "../src/hooks/useRecommendations";

function Harness() {
  const [condition, setCondition] = useState("A");
  const [enabled, setEnabled] = useState(true);
  const state = useRecommendations(enabled, false, {
    condition, followup_answers: [], expertPreference: "system", visitIntent: "",
    routingPreferences: {}, favoriteDoctorIds: [], location: { source: "unknown" },
  });
  return <>
    <button onClick={() => setCondition("A")}>Switch A</button>
    <button onClick={() => setCondition("B")}>Switch B</button>
    <button onClick={() => setEnabled(false)}>Disable</button>
    <button onClick={() => setEnabled(true)}>Enable</button>
    <output data-testid="loading">{String(state.loading)}</output>
    <output data-testid="data">{state.data?.condition ?? "empty"}</output>
    <output data-testid="error">{state.error?.code ?? "none"}</output>
  </>;
}

const harness = <Harness />;
createRoot(document.getElementById("root")!).render(
  new URLSearchParams(location.search).has("strict") ? <StrictMode>{harness}</StrictMode> : harness,
);
