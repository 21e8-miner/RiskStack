import Providers from "./providers";
import { useRisk } from "./hooks/useRisk";
import { useMonteCarlo } from "./hooks/useMonteCarlo";

function RiskPane() {
    const { data, isLoading, error } = useRisk(1);

    if (isLoading) return <div>loading risk</div>;
    if (error) return <div>error</div>;
    if (!data) return <div>no data</div>;

    return (
        <div>
            <div>risk_score: {data.risk_score.toFixed(2)}</div>
            <div>as_of: {data.snapshot.as_of}</div>
        </div>
    );
}

function MCPane() {
    const { data, isLoading, error } = useMonteCarlo(1, 10, 10000);

    if (isLoading) return <div>loading mc</div>;
    if (error) return <div>error</div>;
    if (!data) return <div>no data</div>;

    return (
        <div>
            <div>p50_terminal: {data.p50_terminal.toFixed(3)}</div>
            <div>prob_shortfall: {data.prob_shortfall.toFixed(4)}</div>
        </div>
    );
}

export default function App() {
    return (
        <Providers>
            <div style={{ padding: 16, fontFamily: "system-ui" }}>
                <h1>RiskStack</h1>
                <RiskPane />
                <MCPane />
            </div>
        </Providers>
    );
}
