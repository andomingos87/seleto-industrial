"use client"

import { useState, useEffect } from "react"
import { Code, Save, RefreshCw, History, AlertTriangle, Loader2 } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import { Skeleton } from "@/components/ui/skeleton"
import { toast } from "sonner"
import {
  usePromptsList,
  usePrompt,
  useSavePrompt,
  usePromptBackups,
  useRestoreBackup,
  useReloadAgent,
} from "@/hooks"

function formatTimestamp(timestamp: string): string {
  // Format: 20260108_153045 -> 08/01/2026 15:30:45
  if (timestamp.length !== 15) return timestamp
  
  const year = timestamp.slice(0, 4)
  const month = timestamp.slice(4, 6)
  const day = timestamp.slice(6, 8)
  const hour = timestamp.slice(9, 11)
  const minute = timestamp.slice(11, 13)
  const second = timestamp.slice(13, 15)
  
  return `${day}/${month}/${year} ${hour}:${minute}:${second}`
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function PromptPage() {
  const [selectedPrompt, setSelectedPrompt] = useState<string>("")
  const [editorContent, setEditorContent] = useState<string>("")
  const [hasChanges, setHasChanges] = useState(false)
  const [confirmSaveOpen, setConfirmSaveOpen] = useState(false)
  const [restoreBackupName, setRestoreBackupName] = useState<string | null>(null)

  const { data: promptsList, isLoading: loadingList } = usePromptsList()
  const { data: prompt, isLoading: loadingPrompt } = usePrompt(selectedPrompt)
  const { data: backups, isLoading: loadingBackups } = usePromptBackups(selectedPrompt)

  const savePrompt = useSavePrompt()
  const restoreBackup = useRestoreBackup()
  const reloadAgent = useReloadAgent()

  // Set first prompt as default
  useEffect(() => {
    if (promptsList?.prompts.length && !selectedPrompt) {
      setSelectedPrompt(promptsList.prompts[0])
    }
  }, [promptsList, selectedPrompt])

  // Update editor content when prompt loads
  useEffect(() => {
    if (prompt?.content) {
      setEditorContent(prompt.content)
      setHasChanges(false)
    }
  }, [prompt])

  const handleContentChange = (value: string) => {
    setEditorContent(value)
    setHasChanges(value !== prompt?.content)
  }

  const handleSave = async () => {
    if (!selectedPrompt) return

    try {
      await savePrompt.mutateAsync({
        name: selectedPrompt,
        data: { content: editorContent },
      })
      toast.success("Prompt salvo com sucesso! Backup criado automaticamente.")
      setHasChanges(false)
      setConfirmSaveOpen(false)
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : "Erro desconhecido"
      if (errorMessage.includes("Invalid XML")) {
        toast.error("XML inválido. Verifique a sintaxe do prompt.")
      } else {
        toast.error("Erro ao salvar prompt")
      }
    }
  }

  const handleRestore = async () => {
    if (!selectedPrompt || !restoreBackupName) return

    try {
      await restoreBackup.mutateAsync({
        name: selectedPrompt,
        data: { backup_name: restoreBackupName },
      })
      toast.success("Backup restaurado com sucesso!")
      setRestoreBackupName(null)
    } catch {
      toast.error("Erro ao restaurar backup")
    }
  }

  const handleReloadAgent = async () => {
    try {
      await reloadAgent.mutateAsync()
      toast.success("Agente recarregado com sucesso!")
    } catch {
      toast.error("Erro ao recarregar agente")
    }
  }

  if (loadingList) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Prompt</h1>
          <p className="text-muted-foreground">Edite o prompt do sistema</p>
        </div>
        <Card>
          <CardContent className="pt-6">
            <Skeleton className="h-[500px] w-full" />
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Prompt</h1>
          <p className="text-muted-foreground">
            Edite o prompt do sistema (apenas para desenvolvedores)
          </p>
        </div>
        <div className="flex gap-2">
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="outline" disabled={!selectedPrompt}>
                <History className="mr-2 h-4 w-4" />
                Backups
              </Button>
            </SheetTrigger>
            <SheetContent>
              <SheetHeader>
                <SheetTitle>Histórico de Backups</SheetTitle>
                <SheetDescription>
                  Restaure uma versão anterior do prompt
                </SheetDescription>
              </SheetHeader>
              <div className="mt-6 space-y-4">
                {loadingBackups ? (
                  <div className="space-y-2">
                    {[1, 2, 3].map((i) => (
                      <Skeleton key={i} className="h-16 w-full" />
                    ))}
                  </div>
                ) : backups?.backups.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-8">
                    Nenhum backup disponível
                  </p>
                ) : (
                  backups?.backups.map((backup) => (
                    <div
                      key={backup.name}
                      className="flex items-center justify-between p-3 border rounded-lg"
                    >
                      <div>
                        <p className="text-sm font-medium">
                          {formatTimestamp(backup.timestamp)}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {formatBytes(backup.size_bytes)}
                        </p>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setRestoreBackupName(backup.name)}
                      >
                        Restaurar
                      </Button>
                    </div>
                  ))
                )}
              </div>
            </SheetContent>
          </Sheet>
          <Button
            variant="outline"
            onClick={handleReloadAgent}
            disabled={reloadAgent.isPending}
          >
            {reloadAgent.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 h-4 w-4" />
            )}
            Recarregar Agente
          </Button>
          <Button
            onClick={() => setConfirmSaveOpen(true)}
            disabled={!hasChanges || savePrompt.isPending}
          >
            {savePrompt.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Save className="mr-2 h-4 w-4" />
            )}
            Salvar
          </Button>
        </div>
      </div>

      {/* Warning */}
      <Card className="border-yellow-500/50 bg-yellow-500/5">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
            <div>
              <p className="font-medium text-yellow-600">Atenção</p>
              <p className="text-sm text-muted-foreground">
                Alterações nos prompts afetam diretamente o comportamento do agente.
                Um backup é criado automaticamente antes de cada salvamento.
                Após salvar, clique em &quot;Recarregar Agente&quot; para aplicar as mudanças.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Editor */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <CardTitle className="flex items-center gap-2">
                <Code className="h-5 w-5" />
                Editor
              </CardTitle>
              <Select
                value={selectedPrompt}
                onValueChange={setSelectedPrompt}
              >
                <SelectTrigger className="w-[250px]">
                  <SelectValue placeholder="Selecione um prompt" />
                </SelectTrigger>
                <SelectContent>
                  {promptsList?.prompts.map((name) => (
                    <SelectItem key={name} value={name}>
                      {name}.xml
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              {hasChanges && (
                <Badge variant="outline" className="bg-yellow-500/10 text-yellow-600 border-yellow-500/20">
                  Não salvo
                </Badge>
              )}
              {prompt && (
                <span className="text-xs text-muted-foreground">
                  {formatBytes(prompt.size_bytes)} • Modificado: {new Date(prompt.last_modified).toLocaleString("pt-BR")}
                </span>
              )}
            </div>
          </div>
          <CardDescription>
            {prompt?.path}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loadingPrompt ? (
            <Skeleton className="h-[500px] w-full" />
          ) : (
            <div className="relative">
              <textarea
                value={editorContent}
                onChange={(e) => handleContentChange(e.target.value)}
                className="w-full h-[500px] font-mono text-sm p-4 bg-muted/50 rounded-lg border resize-none focus:outline-none focus:ring-2 focus:ring-ring"
                spellCheck={false}
              />
              <div className="absolute bottom-2 right-2 text-xs text-muted-foreground">
                {editorContent.length} caracteres • {editorContent.split("\n").length} linhas
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Save Confirmation */}
      <AlertDialog open={confirmSaveOpen} onOpenChange={setConfirmSaveOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Salvar alterações?</AlertDialogTitle>
            <AlertDialogDescription>
              Um backup do prompt atual será criado automaticamente.
              Após salvar, você precisará clicar em &quot;Recarregar Agente&quot; para aplicar as mudanças.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleSave}>
              Salvar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Restore Confirmation */}
      <AlertDialog open={!!restoreBackupName} onOpenChange={() => setRestoreBackupName(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Restaurar backup?</AlertDialogTitle>
            <AlertDialogDescription>
              O prompt atual será substituído pela versão do backup.
              Um backup do estado atual será criado antes da restauração.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleRestore}>
              Restaurar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
