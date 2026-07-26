import { Document, Page, Text, View, StyleSheet, renderToBuffer } from "@react-pdf/renderer";
import type { CVData } from "./docx-generator";

// Helvetica es una de las 14 fuentes base de PDF (no requiere embeber archivos ni
// registrarla), máxima compatibilidad con parsers ATS.
const ACCENT = "#4f46e5"; // indigo-600, mismo acento que la marca de la app

const styles = StyleSheet.create({
  page: {
    paddingTop: 40,
    paddingBottom: 40,
    paddingHorizontal: 48,
    fontFamily: "Helvetica",
    fontSize: 10.5,
    color: "#1a1a1a",
  },
  name: {
    fontSize: 22,
    fontFamily: "Helvetica-Bold",
    textAlign: "center",
    color: ACCENT,
    marginBottom: 4,
  },
  contact: {
    fontSize: 9.5,
    textAlign: "center",
    color: "#555555",
    marginBottom: 18,
  },
  sectionTitle: {
    fontSize: 11,
    fontFamily: "Helvetica-Bold",
    color: ACCENT,
    textTransform: "uppercase",
    letterSpacing: 0.5,
    borderBottomWidth: 1,
    borderBottomColor: ACCENT,
    paddingBottom: 3,
    marginTop: 14,
    marginBottom: 8,
  },
  summary: {
    fontSize: 10.5,
    lineHeight: 1.45,
  },
  jobHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 1,
  },
  jobTitle: {
    fontFamily: "Helvetica-Bold",
    fontSize: 11,
  },
  jobDates: {
    fontSize: 9.5,
    color: "#666666",
  },
  jobCompany: {
    fontSize: 10.5,
    fontFamily: "Helvetica-Oblique",
    marginBottom: 4,
  },
  achievement: {
    flexDirection: "row",
    marginBottom: 3,
    paddingLeft: 4,
  },
  bullet: {
    width: 10,
    fontSize: 10.5,
  },
  achievementText: {
    flex: 1,
    fontSize: 10.5,
    lineHeight: 1.4,
  },
  jobBlock: {
    marginBottom: 10,
  },
  eduRow: {
    marginBottom: 4,
    fontSize: 10.5,
  },
  eduDegree: {
    fontFamily: "Helvetica-Bold",
    fontSize: 10.5,
  },
  eduInstitution: {
    fontSize: 10.5,
  },
  eduDate: {
    fontSize: 9.5,
    color: "#666666",
  },
  skills: {
    fontSize: 10.5,
    lineHeight: 1.5,
  },
});

function CvDocument({ data }: { data: CVData }) {
  const contactLine = [data.personalInfo.location, data.personalInfo.email, data.personalInfo.phone, data.personalInfo.linkedin]
    .filter(Boolean)
    .join("  |  ");

  return (
    <Document>
      <Page size="A4" style={styles.page}>
        <Text style={styles.name}>{data.personalInfo.name}</Text>
        {contactLine && <Text style={styles.contact}>{contactLine}</Text>}

        {data.summary && (
          <>
            <Text style={styles.sectionTitle}>Resumen Profesional</Text>
            <Text style={styles.summary}>{data.summary}</Text>
          </>
        )}

        {data.experience.length > 0 && (
          <>
            <Text style={styles.sectionTitle}>Experiencia Profesional</Text>
            {data.experience.map((job, i) => (
              <View key={i} style={styles.jobBlock} wrap={false}>
                <View style={styles.jobHeader}>
                  <Text style={styles.jobTitle}>{job.position}</Text>
                  <Text style={styles.jobDates}>{job.startDate} — {job.endDate}</Text>
                </View>
                <Text style={styles.jobCompany}>{job.company}</Text>
                {job.achievements.map((ach, j) => (
                  <View key={j} style={styles.achievement}>
                    <Text style={styles.bullet}>•</Text>
                    <Text style={styles.achievementText}>{ach}</Text>
                  </View>
                ))}
              </View>
            ))}
          </>
        )}

        {data.education.length > 0 && (
          <>
            <Text style={styles.sectionTitle}>Educación</Text>
            {data.education.map((edu, i) => (
              <Text key={i} style={styles.eduRow}>
                <Text style={styles.eduDegree}>{edu.degree}</Text>
                <Text style={styles.eduInstitution}>{`  —  ${edu.institution}`}</Text>
                <Text style={styles.eduDate}>{`  (${edu.graduationDate})`}</Text>
              </Text>
            ))}
          </>
        )}

        {data.skills.length > 0 && (
          <>
            <Text style={styles.sectionTitle}>Habilidades y Tecnologías</Text>
            <Text style={styles.skills}>{data.skills.join("  •  ")}</Text>
          </>
        )}
      </Page>
    </Document>
  );
}

export class PdfGenerator {
  /** Genera un PDF de una columna, con texto real seleccionable (ATS-friendly). */
  public static async generateCV(data: CVData): Promise<Buffer> {
    return renderToBuffer(<CvDocument data={data} />);
  }
}
