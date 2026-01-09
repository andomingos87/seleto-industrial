"use client"

import { BookOpen } from "lucide-react"

export default function DocsPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh]">
      <div className="rounded-full bg-muted p-6 mb-6">
        <BookOpen className="h-16 w-16 text-muted-foreground" />
      </div>
      <h1 className="text-3xl font-bold tracking-tight mb-2">Documentação</h1>
      <p className="text-muted-foreground text-lg">Em breve</p>
      <p className="text-sm text-muted-foreground mt-4 max-w-md text-center">
        Esta seção conterá a documentação completa do sistema, incluindo guias de uso,
        referências de API e tutoriais.
      </p>
    </div>
  )
}
