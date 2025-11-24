import { useCallback, useMemo, useState } from "react";
import { fetchGraphs } from "../api";
/**
 * Centralises graph collection state (list, selection, loading/error flags).
 * Keeping this logic in one hook keeps the main App component focused on UI wiring.
 */
export function useGraphWorkspace(initialGraphId) {
    const [graphs, setGraphs] = useState([]);
    const [selectedGraphId, setSelectedGraphId] = useState(initialGraphId);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const selectedGraph = useMemo(() => graphs.find((graph) => graph.id === selectedGraphId) ?? null, [graphs, selectedGraphId]);
    const loadGraphs = useCallback(async (preserveSelection = true) => {
        setIsLoading(true);
        setError(null);
        try {
            const data = await fetchGraphs();
            setGraphs(data);
            if (preserveSelection && selectedGraphId) {
                const stillExists = data.some((graph) => graph.id === selectedGraphId);
                if (!stillExists) {
                    setSelectedGraphId(data[0]?.id ?? null);
                }
            }
            else if (data.length > 0) {
                setSelectedGraphId(data[0].id);
            }
            else {
                setSelectedGraphId(null);
            }
        }
        catch (err) {
            setError(err instanceof Error ? err.message : "Unknown error");
        }
        finally {
            setIsLoading(false);
        }
    }, [selectedGraphId]);
    return {
        graphs,
        selectedGraphId,
        selectedGraph,
        isLoading,
        error,
        setError,
        setSelectedGraphId,
        loadGraphs,
    };
}
