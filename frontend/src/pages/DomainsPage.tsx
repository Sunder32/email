import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getDomains, createDomain, deleteDomain } from "@/api/domains";
import { createMailbox, deleteMailbox, testMailbox } from "@/api/mailboxes";
import Button from "@/components/common/Button";
import Input from "@/components/common/Input";
import Modal from "@/components/common/Modal";
import Spinner from "@/components/common/Spinner";
import Badge from "@/components/common/Badge";
import ConfirmDialog from "@/components/common/ConfirmDialog";
import { Plus, Trash2, FlaskConical, ChevronDown, ChevronRight } from "lucide-react";
import toast from "react-hot-toast";
import { handleError } from "@/utils/errors";
import type { MailboxCreate } from "@/types/domain";

export default function DomainsPage() {
  const qc = useQueryClient();
  const { data: domains, isLoading } = useQuery({ queryKey: ["domains"], queryFn: getDomains });
  const [showAddDomain, setShowAddDomain] = useState(false);
  const [showAddMailbox, setShowAddMailbox] = useState<number | null>(null);
  const [expanded, setExpanded] = useState<Set<number>>(new Set());
  const [deleteTarget, setDeleteTarget] = useState<{ type: "domain" | "mailbox"; id: number } | null>(null);

  const addDomainMut = useMutation({
    mutationFn: (data: { name: string; hourly_limit: number; daily_limit: number }) => createDomain(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["domains"] });
      setShowAddDomain(false);
      toast.success("Домен добавлен");
    },
    onError: (e) => handleError(e),
  });

  const addMailboxMut = useMutation({
    mutationFn: ({ domainId, data }: { domainId: number; data: MailboxCreate }) => createMailbox(domainId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["domains"] });
      setShowAddMailbox(null);
      toast.success("Ящик добавлен");
    },
    onError: (e) => handleError(e),
  });

  const deleteMut = useMutation({
    mutationFn: async () => {
      if (!deleteTarget) return;
      if (deleteTarget.type === "domain") {
        await deleteDomain(deleteTarget.id);
      } else {
        await deleteMailbox(deleteTarget.id);
      }
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["domains"] });
      setDeleteTarget(null);
      toast.success("Удалено");
    },
  });

  const testMut = useMutation({
    mutationFn: testMailbox,
    onSuccess: (res) => {
      if (res.success) toast.success(res.message);
      else toast.error(res.message);
    },
    onError: () => toast.error("Ошибка тестирования"),
  });

  const toggle = (id: number) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  if (isLoading) return <Spinner />;

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Домены и ящики</h1>
        <Button onClick={() => setShowAddDomain(true)}>
          <Plus className="h-4 w-4" /> Добавить домен
        </Button>
      </div>

      <div className="space-y-3">
        {domains?.map((domain) => (
          <div key={domain.id} className="rounded-xl border border-gray-200 bg-white">
            <div
              className="flex cursor-pointer items-center justify-between px-6 py-4"
              onClick={() => toggle(domain.id)}
            >
              <div className="flex items-center gap-3">
                {expanded.has(domain.id) ? (
                  <ChevronDown className="h-5 w-5 text-gray-400" />
                ) : (
                  <ChevronRight className="h-5 w-5 text-gray-400" />
                )}
                <div>
                  <span className="font-semibold text-gray-900">{domain.name}</span>
                  <span className="ml-3 text-sm text-gray-500">
                    {domain.mailboxes.length} ящиков
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-500">
                  {domain.sent_today}/{domain.daily_limit} сегодня
                </span>
                <Badge
                  label={domain.is_active ? "Активен" : "Выключен"}
                  color={domain.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}
                />
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setDeleteTarget({ type: "domain", id: domain.id });
                  }}
                  className="rounded-lg p-1.5 text-gray-400 hover:bg-red-50 hover:text-red-500"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>

            {expanded.has(domain.id) && (
              <div className="border-t border-gray-100 px-6 py-4">
                {domain.mailboxes.length > 0 ? (
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-gray-500">
                        <th className="pb-2 font-medium">Email</th>
                        <th className="pb-2 font-medium">SMTP</th>
                        <th className="pb-2 font-medium">Отправлено</th>
                        <th className="pb-2 font-medium">Статус</th>
                        <th className="pb-2" />
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {domain.mailboxes.map((mb) => (
                        <tr key={mb.id}>
                          <td className="py-2.5 font-medium text-gray-900">{mb.email}</td>
                          <td className="py-2.5 text-gray-500">
                            {mb.smtp_host}:{mb.smtp_port}
                          </td>
                          <td className="py-2.5 text-gray-500">
                            {mb.sent_today}/{mb.daily_limit}
                          </td>
                          <td className="py-2.5">
                            <Badge
                              label={mb.is_active ? "Активен" : "Выкл"}
                              color={mb.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}
                            />
                          </td>
                          <td className="py-2.5 text-right">
                            <div className="flex justify-end gap-1">
                              <button
                                onClick={() => testMut.mutate(mb.id)}
                                className="rounded-lg p-1.5 text-gray-400 hover:bg-blue-50 hover:text-blue-500"
                                title="Тестировать"
                              >
                                <FlaskConical className="h-4 w-4" />
                              </button>
                              <button
                                onClick={() => setDeleteTarget({ type: "mailbox", id: mb.id })}
                                className="rounded-lg p-1.5 text-gray-400 hover:bg-red-50 hover:text-red-500"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p className="text-sm text-gray-400">Нет ящиков</p>
                )}
                <Button
                  variant="secondary"
                  size="sm"
                  className="mt-3"
                  onClick={() => setShowAddMailbox(domain.id)}
                >
                  <Plus className="h-3.5 w-3.5" /> Добавить ящик
                </Button>
              </div>
            )}
          </div>
        ))}
      </div>

      <AddDomainModal
        open={showAddDomain}
        onClose={() => setShowAddDomain(false)}
        onSubmit={(data) => addDomainMut.mutate(data)}
        loading={addDomainMut.isPending}
      />

      <AddMailboxModal
        open={showAddMailbox !== null}
        onClose={() => setShowAddMailbox(null)}
        onSubmit={(data) => showAddMailbox && addMailboxMut.mutate({ domainId: showAddMailbox, data })}
        loading={addMailboxMut.isPending}
      />

      <ConfirmDialog
        open={deleteTarget !== null}
        onClose={() => setDeleteTarget(null)}
        onConfirm={() => deleteMut.mutate()}
        title="Удалить?"
        message="Это действие нельзя отменить."
        confirmLabel="Удалить"
        loading={deleteMut.isPending}
      />
    </div>
  );
}

function AddDomainModal({
  open,
  onClose,
  onSubmit,
  loading,
}: {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: { name: string; hourly_limit: number; daily_limit: number }) => void;
  loading: boolean;
}) {
  const [name, setName] = useState("");
  const [hourly, setHourly] = useState(100);
  const [daily, setDaily] = useState(1000);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ name, hourly_limit: hourly, daily_limit: daily });
  };

  return (
    <Modal open={open} onClose={onClose} title="Добавить домен">
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input label="Домен" value={name} onChange={(e) => setName(e.target.value)} placeholder="company.ru" required />
        <div className="grid grid-cols-2 gap-4">
          <Input label="Лимит/час" type="number" value={hourly} onChange={(e) => setHourly(+e.target.value)} />
          <Input label="Лимит/день" type="number" value={daily} onChange={(e) => setDaily(+e.target.value)} />
        </div>
        <div className="flex justify-end gap-3">
          <Button variant="secondary" onClick={onClose}>Отмена</Button>
          <Button type="submit" loading={loading}>Добавить</Button>
        </div>
      </form>
    </Modal>
  );
}

function AddMailboxModal({
  open,
  onClose,
  onSubmit,
  loading,
}: {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: MailboxCreate) => void;
  loading: boolean;
}) {
  const [form, setForm] = useState({
    email: "",
    smtp_host: "",
    smtp_port: 587,
    login: "",
    password: "",
    use_tls: true,
    hourly_limit: 50,
    daily_limit: 500,
  });

  const set = (key: string, val: any) => setForm((p) => ({ ...p, [key]: val }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(form);
  };

  return (
    <Modal open={open} onClose={onClose} title="Добавить ящик">
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input label="Email" value={form.email} onChange={(e) => set("email", e.target.value)} required />
        <div className="grid grid-cols-2 gap-4">
          <Input label="SMTP Host" value={form.smtp_host} onChange={(e) => set("smtp_host", e.target.value)} required />
          <Input label="SMTP Port" type="number" value={form.smtp_port} onChange={(e) => set("smtp_port", +e.target.value)} />
        </div>
        <Input label="Логин" value={form.login} onChange={(e) => set("login", e.target.value)} required />
        <Input label="Пароль" type="password" value={form.password} onChange={(e) => set("password", e.target.value)} required />
        <div className="grid grid-cols-2 gap-4">
          <Input label="Лимит/час" type="number" value={form.hourly_limit} onChange={(e) => set("hourly_limit", +e.target.value)} />
          <Input label="Лимит/день" type="number" value={form.daily_limit} onChange={(e) => set("daily_limit", +e.target.value)} />
        </div>
        <div className="flex justify-end gap-3">
          <Button variant="secondary" onClick={onClose}>Отмена</Button>
          <Button type="submit" loading={loading}>Добавить</Button>
        </div>
      </form>
    </Modal>
  );
}
