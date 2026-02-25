export type Client = { id: number; name: string; email?: string | null };
export type Position = { ticker: string; weight: number; kind: string };
export type Portfolio = { id: number; client_id: number; name: string; base_ccy: string; positions: Position[] };

export type AuthResp = { token: string };
export type ProposalResp = { proposal_run_id: number; artifact_id: number; filename: string };
