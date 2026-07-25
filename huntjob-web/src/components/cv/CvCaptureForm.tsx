"use client";

import { useState } from "react";
import { Loader2, Plus, Trash2, UploadCloud, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import type { CVData } from "@/lib/document/docx-generator";

interface CvCaptureFormProps {
  onComplete: (cvData: CVData) => void;
  onCancel: () => void;
}

const EMPTY_CV: CVData = {
  personalInfo: { name: "", email: "", phone: "", linkedin: "", location: "" },
  summary: "",
  experience: [],
  education: [],
  skills: [],
};

export function CvCaptureForm({ onComplete, onCancel }: CvCaptureFormProps) {
  const [step, setStep] = useState<"upload" | "edit">("upload");
  const [parsing, setParsing] = useState(false);
  const [parseError, setParseError] = useState("");
  const [cv, setCv] = useState<CVData>(EMPTY_CV);
  const [skillsText, setSkillsText] = useState("");
  const [formError, setFormError] = useState("");

  const handleFileUpload = async (file: globalThis.File) => {
    setParsing(true);
    setParseError("");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch("/api/cv/parse", { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) {
        setParseError(data.error || "No pudimos leer tu PDF.");
        setCv(EMPTY_CV);
        setSkillsText("");
      } else {
        setCv(data.cvData as CVData);
        setSkillsText(((data.cvData as CVData).skills || []).join(", "));
      }
    } catch {
      setParseError("No pudimos leer tu PDF.");
      setCv(EMPTY_CV);
      setSkillsText("");
    } finally {
      setParsing(false);
      setStep("edit");
    }
  };

  const handleSkipUpload = () => {
    setCv(EMPTY_CV);
    setSkillsText("");
    setStep("edit");
  };

  const updatePersonalInfo = (field: keyof CVData["personalInfo"], value: string) => {
    setCv((prev) => ({ ...prev, personalInfo: { ...prev.personalInfo, [field]: value } }));
  };

  const addExperience = () => {
    setCv((prev) => ({
      ...prev,
      experience: [...prev.experience, { company: "", position: "", startDate: "", endDate: "", achievements: [""] }],
    }));
  };

  const updateExperience = (
    index: number,
    field: "company" | "position" | "startDate" | "endDate",
    value: string
  ) => {
    setCv((prev) => ({
      ...prev,
      experience: prev.experience.map((exp, i) => (i === index ? { ...exp, [field]: value } : exp)),
    }));
  };

  const updateAchievement = (expIndex: number, achIndex: number, value: string) => {
    setCv((prev) => ({
      ...prev,
      experience: prev.experience.map((exp, i) =>
        i === expIndex
          ? { ...exp, achievements: exp.achievements.map((a, j) => (j === achIndex ? value : a)) }
          : exp
      ),
    }));
  };

  const addAchievement = (expIndex: number) => {
    setCv((prev) => ({
      ...prev,
      experience: prev.experience.map((exp, i) =>
        i === expIndex ? { ...exp, achievements: [...exp.achievements, ""] } : exp
      ),
    }));
  };

  const removeExperience = (index: number) => {
    setCv((prev) => ({ ...prev, experience: prev.experience.filter((_, i) => i !== index) }));
  };

  const addEducation = () => {
    setCv((prev) => ({
      ...prev,
      education: [...prev.education, { institution: "", degree: "", graduationDate: "" }],
    }));
  };

  const updateEducation = (
    index: number,
    field: "institution" | "degree" | "graduationDate",
    value: string
  ) => {
    setCv((prev) => ({
      ...prev,
      education: prev.education.map((edu, i) => (i === index ? { ...edu, [field]: value } : edu)),
    }));
  };

  const removeEducation = (index: number) => {
    setCv((prev) => ({ ...prev, education: prev.education.filter((_, i) => i !== index) }));
  };

  const handleSubmit = () => {
    if (!cv.personalInfo.name.trim() || !cv.personalInfo.email.trim()) {
      setFormError("Nombre y email son obligatorios.");
      return;
    }
    setFormError("");
    const skills = skillsText.split(",").map((s) => s.trim()).filter(Boolean);
    onComplete({ ...cv, skills });
  };

  if (step === "upload") {
    return (
      <Card className="bg-zinc-900/60 border-white/10">
        <CardHeader>
          <CardTitle className="text-white">Completa tu CV base</CardTitle>
          <CardDescription>
            Es tu primera postulación — sube tu CV en PDF y la IA lo va a leer, o complétalo a mano.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {parseError && (
            <p className="text-sm text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded-lg p-3">
              {parseError}
            </p>
          )}
          <label className="flex flex-col items-center justify-center gap-2 border-2 border-dashed border-white/10 rounded-xl p-8 cursor-pointer hover:border-indigo-500/50 transition-colors">
            {parsing ? (
              <>
                <Loader2 className="h-8 w-8 text-indigo-400 animate-spin" />
                <span className="text-sm text-zinc-400">Analizando tu CV con IA...</span>
              </>
            ) : (
              <>
                <UploadCloud className="h-8 w-8 text-zinc-500" />
                <span className="text-sm text-zinc-400">Haz clic para subir tu CV (PDF, máx. 4MB)</span>
              </>
            )}
            <input
              type="file"
              accept="application/pdf"
              className="hidden"
              disabled={parsing}
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleFileUpload(file);
              }}
            />
          </label>
          <div className="flex justify-between items-center">
            <Button variant="ghost" onClick={onCancel} disabled={parsing}>
              Cancelar
            </Button>
            <Button variant="outline" onClick={handleSkipUpload} disabled={parsing}>
              <FileText className="mr-2 h-4 w-4" /> Completar a mano
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-zinc-900/60 border-white/10">
      <CardHeader>
        <CardTitle className="text-white">Revisa y confirma tu CV base</CardTitle>
        <CardDescription>
          Corrige lo que necesites. Esto se guarda como tu CV base para futuras postulaciones.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {parseError && (
          <p className="text-sm text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded-lg p-3">
            {parseError}
          </p>
        )}
        {formError && <p className="text-sm text-rose-400">{formError}</p>}

        <div className="grid sm:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Nombre completo</Label>
            <Input value={cv.personalInfo.name} onChange={(e) => updatePersonalInfo("name", e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>Email</Label>
            <Input value={cv.personalInfo.email} onChange={(e) => updatePersonalInfo("email", e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>Teléfono</Label>
            <Input value={cv.personalInfo.phone} onChange={(e) => updatePersonalInfo("phone", e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>LinkedIn</Label>
            <Input value={cv.personalInfo.linkedin} onChange={(e) => updatePersonalInfo("linkedin", e.target.value)} />
          </div>
          <div className="space-y-2 sm:col-span-2">
            <Label>Ubicación</Label>
            <Input value={cv.personalInfo.location} onChange={(e) => updatePersonalInfo("location", e.target.value)} />
          </div>
        </div>

        <div className="space-y-2">
          <Label>Resumen profesional</Label>
          <Textarea
            value={cv.summary}
            onChange={(e) => setCv((prev) => ({ ...prev, summary: e.target.value }))}
            rows={3}
          />
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label>Experiencia</Label>
            <Button type="button" variant="outline" size="sm" onClick={addExperience}>
              <Plus className="h-4 w-4 mr-1" /> Agregar
            </Button>
          </div>
          {cv.experience.map((exp, i) => (
            <div key={i} className="border border-white/10 rounded-xl p-4 space-y-3">
              <div className="flex justify-end">
                <button type="button" onClick={() => removeExperience(i)} className="text-zinc-500 hover:text-rose-400">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
              <div className="grid sm:grid-cols-2 gap-3">
                <Input placeholder="Empresa" value={exp.company} onChange={(e) => updateExperience(i, "company", e.target.value)} />
                <Input placeholder="Cargo" value={exp.position} onChange={(e) => updateExperience(i, "position", e.target.value)} />
                <Input placeholder="Inicio (ej. Ene 2021)" value={exp.startDate} onChange={(e) => updateExperience(i, "startDate", e.target.value)} />
                <Input placeholder="Fin (ej. Presente)" value={exp.endDate} onChange={(e) => updateExperience(i, "endDate", e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label className="text-xs">Logros</Label>
                {exp.achievements.map((ach, j) => (
                  <Input
                    key={j}
                    placeholder="Ej. Lideré la migración a Next.js reduciendo el TTI en 40%"
                    value={ach}
                    onChange={(e) => updateAchievement(i, j, e.target.value)}
                  />
                ))}
                <Button type="button" variant="ghost" size="sm" onClick={() => addAchievement(i)}>
                  <Plus className="h-3 w-3 mr-1" /> Agregar logro
                </Button>
              </div>
            </div>
          ))}
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label>Educación</Label>
            <Button type="button" variant="outline" size="sm" onClick={addEducation}>
              <Plus className="h-4 w-4 mr-1" /> Agregar
            </Button>
          </div>
          {cv.education.map((edu, i) => (
            <div key={i} className="border border-white/10 rounded-xl p-4 space-y-3">
              <div className="flex justify-end">
                <button type="button" onClick={() => removeEducation(i)} className="text-zinc-500 hover:text-rose-400">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
              <div className="grid sm:grid-cols-3 gap-3">
                <Input placeholder="Institución" value={edu.institution} onChange={(e) => updateEducation(i, "institution", e.target.value)} />
                <Input placeholder="Título" value={edu.degree} onChange={(e) => updateEducation(i, "degree", e.target.value)} />
                <Input placeholder="Año" value={edu.graduationDate} onChange={(e) => updateEducation(i, "graduationDate", e.target.value)} />
              </div>
            </div>
          ))}
        </div>

        <div className="space-y-2">
          <Label>Skills (separadas por coma)</Label>
          <Input value={skillsText} onChange={(e) => setSkillsText(e.target.value)} placeholder="React, TypeScript, Node.js" />
        </div>

        <div className="flex justify-between items-center pt-2">
          <Button variant="ghost" onClick={onCancel}>
            Cancelar
          </Button>
          <Button onClick={handleSubmit}>Guardar y continuar</Button>
        </div>
      </CardContent>
    </Card>
  );
}
