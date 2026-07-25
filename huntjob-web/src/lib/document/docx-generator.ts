import { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, convertInchesToTwip } from "docx";

export interface CVData {
  personalInfo: {
    name: string;
    email: string;
    phone: string;
    linkedin?: string;
    location?: string;
  };
  summary: string;
  experience: {
    company: string;
    position: string;
    startDate: string;
    endDate: string;
    achievements: string[]; // Viñetas en formato CAR
  }[];
  education: {
    institution: string;
    degree: string;
    graduationDate: string;
  }[];
  skills: string[];
}

export class DocxGenerator {
  
  /**
   * Genera un documento Word optimizado para ATS.
   * Retorna un Buffer con el contenido del archivo .docx.
   */
  public static async generateCV(data: CVData): Promise<Buffer> {
    const doc = new Document({
      sections: [
        {
          properties: {
            page: {
              margin: {
                top: convertInchesToTwip(1),
                bottom: convertInchesToTwip(1),
                left: convertInchesToTwip(1),
                right: convertInchesToTwip(1),
              },
            },
          },
          children: [
            // --- HEADER ---
            new Paragraph({
              alignment: AlignmentType.CENTER,
              heading: HeadingLevel.HEADING_1,
              children: [
                new TextRun({
                  text: data.personalInfo.name,
                  bold: true,
                  size: 32, // 16pt
                  font: "Arial",
                }),
              ],
            }),
            new Paragraph({
              alignment: AlignmentType.CENTER,
              spacing: { after: 300 },
              children: [
                new TextRun({
                  text: `${data.personalInfo.location ? data.personalInfo.location + ' | ' : ''}${data.personalInfo.email} | ${data.personalInfo.phone}${data.personalInfo.linkedin ? ' | ' + data.personalInfo.linkedin : ''}`,
                  size: 20, // 10pt
                  font: "Arial",
                }),
              ],
            }),

            // --- PROFESSIONAL SUMMARY ---
            this.createSectionTitle("PROFESSIONAL SUMMARY"),
            new Paragraph({
              spacing: { after: 200 },
              children: [
                new TextRun({
                  text: data.summary,
                  size: 22, // 11pt
                  font: "Arial",
                }),
              ],
            }),

            // --- EXPERIENCE ---
            this.createSectionTitle("PROFESSIONAL EXPERIENCE"),
            ...data.experience.flatMap((job) => [
              new Paragraph({
                spacing: { before: 100, after: 50 },
                children: [
                  new TextRun({
                    text: job.position,
                    bold: true,
                    size: 24,
                    font: "Arial",
                  }),
                  new TextRun({
                    text: ` | ${job.company}`,
                    italics: true,
                    size: 24,
                    font: "Arial",
                  }),
                ],
              }),
              new Paragraph({
                spacing: { after: 100 },
                children: [
                  new TextRun({
                    text: `${job.startDate} - ${job.endDate}`,
                    size: 20,
                    font: "Arial",
                    color: "666666",
                  }),
                ],
              }),
              // Logros (CAR format)
              ...job.achievements.map((achievement) =>
                new Paragraph({
                  text: achievement,
                  bullet: {
                    level: 0,
                  },
                  spacing: { after: 50 },
                  style: "Normal",
                })
              ),
              // Espaciador entre trabajos
              new Paragraph({ spacing: { after: 200 }, children: [] }),
            ]),

            // --- EDUCATION ---
            this.createSectionTitle("EDUCATION"),
            ...data.education.map((edu) =>
              new Paragraph({
                spacing: { before: 100, after: 100 },
                children: [
                  new TextRun({
                    text: `${edu.degree} - `,
                    bold: true,
                    size: 22,
                    font: "Arial",
                  }),
                  new TextRun({
                    text: edu.institution,
                    size: 22,
                    font: "Arial",
                  }),
                  new TextRun({
                    text: ` (${edu.graduationDate})`,
                    size: 20,
                    font: "Arial",
                    color: "666666",
                  }),
                ],
              })
            ),

            // --- SKILLS ---
            new Paragraph({ spacing: { after: 200 }, children: [] }), // Espaciador adicional
            this.createSectionTitle("SKILLS & TECHNOLOGIES"),
            new Paragraph({
              spacing: { after: 200 },
              children: [
                new TextRun({
                  text: data.skills.join(" • "),
                  size: 22,
                  font: "Arial",
                }),
              ],
            }),
          ],
        },
      ],
      styles: {
        paragraphStyles: [
          {
            id: "Normal",
            name: "Normal",
            basedOn: "Normal",
            next: "Normal",
            run: {
              size: 22, // 11pt
              font: "Arial",
            },
          },
        ],
      },
    });

    // Retorna un Buffer en backend
    return await Packer.toBuffer(doc);
  }

  /**
   * Helper para títulos de sección (ATS friendly)
   */
  private static createSectionTitle(title: string): Paragraph {
    return new Paragraph({
      heading: HeadingLevel.HEADING_2,
      spacing: { before: 200, after: 100 },
      border: {
        bottom: {
          color: "000000",
          space: 1,
          value: "single",
          size: 6,
        },
      },
      children: [
        new TextRun({
          text: title.toUpperCase(),
          bold: true,
          size: 24, // 12pt
          font: "Arial",
          color: "000000",
        }),
      ],
    });
  }
}
