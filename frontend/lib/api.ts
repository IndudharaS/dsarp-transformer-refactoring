export const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000";

export type StoredFile = {
  originalName: string;
  storedPath: string;
};

export type RunRecord = {
  runId: string;
  projectName: string;
  systemName: string;
  version: string;
  status: string;
  selectedSmells: string[];
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
  totalProcessed?: number;
  recommendationsGenerated?: number;
  error?: string | null;
  databaseVerified: boolean;
  uploadedFiles: {
    runId: string;
    files: Record<string, StoredFile>;
    createdAt: string;
  } | null;
};

export type AnalyzeResponse = {
  runId: string;
  status: string;
  totalProcessed: number;
  recommendationsGenerated: number;
};

export type Recommendation = {
  runId: string;
  system: string;
  version: string;
  smellId: string;
  smellType: string;
  affectedElements: string[];
  severity: number;
  size: number;
  strength: number;
  instabilityGap: number;
  numberOfEdges: number;
  predictedStrategy: string;
  classifierConfidence: number;
  classifierModel: string;
  recommendation: string;
  targetComponents: string[];
  reason: string;
  risk: string;
  steps: string[];
  expectedImpact: string;
  testingAdvice: string;
  recommendationConfidence: number;
  smellPriorityScore: number;
  recommendationQualityScore: number;
  finalRankingScore: number;
  rankLevel: string;
  rankPosition: number;
  promptVersion: string;
  modelUsed: string;
  usedFallback: boolean;
  createdAt: string;
};

export type StatsResponse = {
  runId: string;
  system: string;
  totalSmellsProcessed: number;
  recommendationsGenerated: number;
  smellsByType: Record<string, number>;
  predictedStrategies: Record<string, number>;
  priorityDistribution: Record<string, number>;
  riskDistribution: Record<string, number>;
  averageSeverityBySmellType: Record<string, number>;
  topRecommendations: Recommendation[];
};

export async function apiFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    cache: "no-store",
    ...options,
  });
  if (!response.ok) throw new Error(await getApiError(response));
  return (await response.json()) as T;
}

export async function getApiError(response: Response): Promise<string> {
  try {
    const body = await response.json();
    const detail = body.detail;
    if (typeof detail === "string") return detail;
    if (detail?.message) {
      const missing = detail.missingColumns
        ? Object.entries(detail.missingColumns)
            .map(([file, columns]) => `${file}: ${(columns as string[]).join(", ")}`)
            .join("; ")
        : "";
      return missing ? `${detail.message} ${missing}` : detail.message;
    }
  } catch {
    // Fall through to the status-based message.
  }
  return `Request failed with status ${response.status}.`;
}
