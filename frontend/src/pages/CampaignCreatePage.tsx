import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createCampaign, startCampaign } from "@/api/campaigns";
import { uploadContacts, validateContacts } from "@/api/contacts";
import { generateVariations } from "@/api/variations";
import Button from "@/components/common/Button";
import Input from "@/components/common/Input";
import Spinner from "@/components/common/Spinner";
import { Upload, Sparkles, CheckCircle, Play } from "lucide-react";
import toast from "react-hot-toast";
import { useDropzone } from "react-dropzone";
import { handleError } from "@/utils/errors";

type Step = "compose" | "upload" | "validate" | "variations" | "launch";

export default function CampaignCreatePage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [step, setStep] = useState<Step>("compose");
  const [campaignId, setCampaignId] = useState<number | null>(null);

  const [name, setName] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [rotateN, setRotateN] = useState(5);
  const [delayMin, setDelayMin] = useState(5);
  const [delayMax, setDelayMax] = useState(30);
  const [skipValidation, setSkipValidation] = useState(false);

  const [uploadResult, setUploadResult] = useState<{ total: number; parsed: number; duplicates: number } | null>(null);

  const createMut = useMutation({
    mutationFn: () =>
      createCampaign({
        name,
        original_subject: subject,
        original_body: body,
        rotate_every_n: rotateN,
        delay_min_sec: delayMin,
        delay_max_sec: delayMax,
        skip_validation: skipValidation,
      }),
    onSuccess: (c) => {
      setCampaignId(c.id);
      setStep("upload");
      toast.success("Кампания создана");
    },
    onError: (e) => handleError(e),
  });

  const uploadMut = useMutation({
    mutationFn: (file: File) => uploadContacts(campaignId!, file),
    onSuccess: (res) => {
      setUploadResult(res);
      setStep("validate");
      toast.success(`Загружено ${res.parsed} контактов`);
    },
    onError: (e) => handleError(e, "Ошибка загрузки"),
  });

  const validateMut = useMutation({
    mutationFn: () => validateContacts(campaignId!),
    onSuccess: () => {
      toast.success("Валидация запущена");
      setStep("variations");
    },
    onError: (e) => handleError(e, "Ошибка валидации"),
  });

  const genMut = useMutation({
    mutationFn: () => generateVariations(campaignId!, 30),
    onSuccess: () => {
      toast.success("Генерация вариаций запущена");
      setStep("launch");
    },
    onError: (e) => handleError(e, "Ошибка генерации вариаций"),
  });

  const startMut = useMutation({
    mutationFn: () => startCampaign(campaignId!),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["campaigns"] });
      navigate(`/campaigns/${campaignId}/monitor`);
    },
    onError: (e) => handleError(e, "Ошибка запуска"),
  });

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { "text/csv": [".csv"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"] },
    maxFiles: 1,
    onDrop: (files) => files[0] && uploadMut.mutate(files[0]),
  });

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Новая рассылка</h1>

      <div className="mb-8 flex gap-2">
        {(["compose", "upload", "validate", "variations", "launch"] as Step[]).map((s, i) => (
          <div
            key={s}
            className={`flex-1 h-1.5 rounded-full ${
              (["compose", "upload", "validate", "variations", "launch"] as Step[]).indexOf(step) >= i
                ? "bg-primary-500"
                : "bg-gray-200"
            }`}
          />
        ))}
      </div>

      {step === "compose" && (
        <div className="space-y-4 rounded-xl border border-gray-200 bg-white p-6">
          <Input label="Название кампании" value={name} onChange={(e) => setName(e.target.value)} required />
          <Input label="Тема письма" value={subject} onChange={(e) => setSubject(e.target.value)} required />
          <div className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">Текст письма (HTML)</label>
            <textarea
              className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none"
              rows={10}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              required
              placeholder="Первый абзац — это «айсберг», он будет варьироваться.&#10;&#10;Остальной текст остаётся неизменным."
            />
            <p className="text-xs text-gray-400">Первый абзац (до пустой строки) будет использоваться как «айсберг» для вариаций</p>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <Input label="Ротация каждые N писем" type="number" value={rotateN} onChange={(e) => setRotateN(+e.target.value)} />
            <Input label="Задержка мин (сек)" type="number" value={delayMin} onChange={(e) => setDelayMin(+e.target.value)} />
            <Input label="Задержка макс (сек)" type="number" value={delayMax} onChange={(e) => setDelayMax(+e.target.value)} />
          </div>
          <label className="flex items-start gap-2 rounded-lg bg-yellow-50 p-3 cursor-pointer">
            <input
              type="checkbox"
              checked={skipValidation}
              onChange={(e) => setSkipValidation(e.target.checked)}
              className="mt-0.5"
            />
            <div className="text-sm">
              <div className="font-medium text-gray-900">Пропустить валидацию адресов</div>
              <div className="text-xs text-gray-600">
                Письма уйдут на все загруженные адреса без проверки. Рекомендуется включить, если вы уверены в списке и валидация ложно блокирует живые адреса (SMTP-проверка ненадёжна с VPS).
              </div>
            </div>
          </label>
          <div className="flex justify-end">
            <Button onClick={() => createMut.mutate()} loading={createMut.isPending}>
              Далее
            </Button>
          </div>
        </div>
      )}

      {step === "upload" && (
        <div className="space-y-4 rounded-xl border border-gray-200 bg-white p-6">
          <h2 className="text-lg font-semibold">Загрузка контактов</h2>
          <div
            {...getRootProps()}
            className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed px-6 py-12 transition ${
              isDragActive ? "border-primary-400 bg-primary-50" : "border-gray-300 hover:border-gray-400"
            }`}
          >
            <input {...getInputProps()} />
            <Upload className="mb-3 h-10 w-10 text-gray-400" />
            <p className="text-sm text-gray-600">
              {isDragActive ? "Отпустите файл" : "Перетащите CSV или XLSX, или нажмите"}
            </p>
          </div>
          {uploadMut.isPending && <Spinner className="h-6 w-6" />}
        </div>
      )}

      {step === "validate" && (
        <div className="space-y-4 rounded-xl border border-gray-200 bg-white p-6">
          <h2 className="text-lg font-semibold">Валидация адресов</h2>
          {uploadResult && (
            <div className="rounded-lg bg-gray-50 p-4 text-sm">
              <p>Загружено: <strong>{uploadResult.parsed}</strong></p>
              <p>Дубликатов: <strong>{uploadResult.duplicates}</strong></p>
            </div>
          )}
          {skipValidation ? (
            <div className="rounded-lg bg-yellow-50 p-4 text-sm text-gray-700">
              Вы выбрали «Пропустить валидацию» — этот шаг можно пропустить.
            </div>
          ) : (
            <p className="text-sm text-gray-500">
              Система проверит каждый email: формат, существование домена, наличие ящика.
              SMTP-проверка с VPS может ложно блокировать живые адреса — если не уверены,
              просто пропустите шаг.
            </p>
          )}
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setStep("variations")}>
              Пропустить
            </Button>
            {!skipValidation && (
              <Button onClick={() => validateMut.mutate()} loading={validateMut.isPending}>
                <CheckCircle className="h-4 w-4" /> Запустить валидацию
              </Button>
            )}
          </div>
        </div>
      )}

      {step === "variations" && (
        <div className="space-y-4 rounded-xl border border-gray-200 bg-white p-6">
          <h2 className="text-lg font-semibold">Генерация вариаций</h2>
          <p className="text-sm text-gray-500">
            AI создаст 30 вариаций темы и первого абзаца. Вы сможете их просмотреть и отредактировать.
          </p>
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setStep("launch")}>
              Пропустить
            </Button>
            <Button onClick={() => genMut.mutate()} loading={genMut.isPending}>
              <Sparkles className="h-4 w-4" /> Сгенерировать
            </Button>
          </div>
        </div>
      )}

      {step === "launch" && (
        <div className="space-y-4 rounded-xl border border-gray-200 bg-white p-6">
          <h2 className="text-lg font-semibold">Запуск рассылки</h2>
          <p className="text-sm text-gray-500">
            Всё готово. Нажмите «Запустить» для начала отправки.
          </p>
          <div className="flex justify-end">
            <Button onClick={() => startMut.mutate()} loading={startMut.isPending}>
              <Play className="h-4 w-4" /> Запустить
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
