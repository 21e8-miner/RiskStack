import { z } from "zod";
import { useQuery } from "@tanstack/react-query";
import { apiGetZod } from "../lib/api";
import { SnapshotSchema } from "./useRisk";

export const MCResultSchema = z.object({
    horizon_years: z.number().positive(),
    n_paths: z.number().int().positive(),
    p10_terminal: z.number().finite(),
    p50_terminal: z.number().finite(),
    p90_terminal: z.number().finite(),
    prob_shortfall: z.number().finite(),
    worst_path_drawdown_p05: z.number().finite(),
    snapshot: SnapshotSchema,
});

export type MCResult = z.infer<typeof MCResultSchema>;

export function useMonteCarlo(portfolioId: number, horizonYears = 10, nPaths = 10000) {
    return useQuery<MCResult>({
        queryKey: ["mc", portfolioId, horizonYears, nPaths],
        queryFn: () =>
            apiGetZod(
                `/v1/analytics/${portfolioId}/montecarlo?horizon_years=${horizonYears}&n_paths=${nPaths}`,
                MCResultSchema
            ),
    });
}
