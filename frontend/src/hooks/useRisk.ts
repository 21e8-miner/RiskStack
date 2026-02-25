import { z } from "zod";
import { useQuery } from "@tanstack/react-query";
import { apiGetZod } from "../lib/api";

export const SnapshotSchema = z.object({
    as_of: z.string().datetime(),
    price_source: z.string(),
    price_range_start: z.string().datetime().nullable().optional(),
    price_range_end: z.string().datetime().nullable().optional(),
    trading_days_analyzed: z.number().int().positive(),
});

export const RiskResultSchema = z.object({
    risk_score: z.number().finite(),
    components: z.record(z.number().finite()),
    max_drawdown: z.number().finite(),
    vol_annual: z.number().finite(),
    downside_vol_annual: z.number().finite(),
    skew: z.number().finite(),
    kurtosis_excess: z.number().finite(),
    snapshot: SnapshotSchema,
});

export type RiskResult = z.infer<typeof RiskResultSchema>;

export function useRisk(portfolioId: number) {
    return useQuery<RiskResult>({
        queryKey: ["risk", portfolioId],
        queryFn: () => apiGetZod(`/v1/analytics/${portfolioId}/risk`, RiskResultSchema),
    });
}
