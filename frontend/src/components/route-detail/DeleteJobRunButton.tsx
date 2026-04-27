import { useMutation, useQueryClient } from "@tanstack/react-query";
import { deleteJobRun } from "../../api/job_runs";
import { formatCamera } from "../../utils/formatters";

interface Props {
  routeId: string;
  jobDefId: number;
  jobRunNum: number;
  camera: string;
}

const BASE_CLASSES =
  "inline-flex items-center justify-center w-4 h-4 p-0 text-[10px] font-bold tracking-[0.07em] whitespace-nowrap border shrink-0 font-[family-name:var(--font-mono)] transition-colors";

const DEFAULT_CLASSES =
  "bg-transparent border-[var(--border-on-inverse-faint)] text-[var(--text-on-inverse-dim)] cursor-pointer hover:border-[var(--accent-alert)] hover:text-[var(--accent-alert)]";

const PENDING_CLASSES =
  "bg-transparent border-[var(--accent-alert)] text-[var(--accent-alert)] cursor-not-allowed opacity-80";

export function DeleteJobRunButton({ routeId, jobDefId, jobRunNum, camera }: Props) {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => deleteJobRun({ routeId, jobDefId, jobRunNum, camera }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobRuns", routeId] });
    },
  });

  const handleClick = () => {
    if (!confirm(`Delete job run #${jobRunNum} (${formatCamera(camera)})? This cannot be undone.`)) return;
    mutation.mutate();
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={mutation.isPending}
      title="Delete job run"
      className={`${BASE_CLASSES} ${mutation.isPending ? PENDING_CLASSES : DEFAULT_CLASSES}`}
    >
      {mutation.isPending ? "…" : "✕"}
    </button>
  );
}
