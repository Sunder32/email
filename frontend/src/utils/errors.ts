import toast from "react-hot-toast";

export function handleError(error: unknown, defaultMsg = "Произошла ошибка"): void {
  const err = error as { response?: { data?: { detail?: string } }; message?: string };
  const detail = err?.response?.data?.detail;
  toast.error(detail || err?.message || defaultMsg);
}

export function extractErrorMessage(error: unknown, defaultMsg = "Произошла ошибка"): string {
  const err = error as { response?: { data?: { detail?: string } }; message?: string };
  return err?.response?.data?.detail || err?.message || defaultMsg;
}
