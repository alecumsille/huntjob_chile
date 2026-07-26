import { createClient } from "@/utils/supabase/client";
import type { CVData } from "@/lib/document/docx-generator";

type SupabaseBrowserClient = ReturnType<typeof createClient>;

/**
 * El "CV base" es la fila de `resumes` con target_company IS NULL.
 * Actualiza esa fila si ya existe (evita duplicados al re-subir el CV);
 * si no existe, crea la primera.
 */
export async function upsertBaseResume(
  supabase: SupabaseBrowserClient,
  userId: string,
  cvData: CVData
) {
  const { data: existing, error: selectError } = await supabase
    .from("resumes")
    .select("id")
    .eq("user_id", userId)
    .is("target_company", null)
    .order("created_at", { ascending: false })
    .limit(1);

  if (selectError) throw selectError;

  if (existing && existing.length > 0) {
    const { error: updateError } = await supabase
      .from("resumes")
      .update({ name: "Mi CV Base", cv_data: cvData })
      .eq("id", existing[0].id);

    if (updateError) throw updateError;
    return;
  }

  const { error: insertError } = await supabase.from("resumes").insert({
    user_id: userId,
    name: "Mi CV Base",
    cv_data: cvData,
  });

  if (insertError) throw insertError;
}
