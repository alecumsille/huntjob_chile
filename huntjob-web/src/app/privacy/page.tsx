import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Políticas de Privacidad | HuntJob Pro",
  description: "Políticas de privacidad y manejo de datos de HuntJob Pro.",
};

export default function PrivacyPage() {
  return (
    <div className="container mx-auto px-4 py-20 max-w-4xl">
      <div className="space-y-8 text-zinc-300">
        <div className="text-center space-y-4 mb-16">
          <h1 className="text-4xl md:text-5xl font-bold font-heading text-transparent bg-clip-text bg-gradient-to-r from-amber-200 to-amber-500">
            Políticas de Privacidad
          </h1>
          <p className="text-zinc-400">Última actualización: 24 de Julio de 2026</p>
        </div>

        <section className="space-y-4">
          <h2 className="text-2xl font-bold font-heading text-white">1. Información que Recopilamos</h2>
          <p>
            En HuntJob Pro recopilamos información personal que tú nos proporcionas directamente al registrarte y utilizar nuestra plataforma. Esto incluye, pero no se limita a: nombre, dirección de correo electrónico, historial laboral, educación, habilidades (tu Currículum Vitae), y cualquier otro dato relevante para la optimización de tu perfil profesional.
          </p>
        </section>

        <section className="space-y-4">
          <h2 className="text-2xl font-bold font-heading text-white">2. Uso de la Información</h2>
          <p>
            Utilizamos la información recopilada principalmente para:
          </p>
          <ul className="list-disc pl-6 space-y-2 text-zinc-400">
            <li>Analizar tu perfil utilizando nuestros motores de Inteligencia Artificial.</li>
            <li>Generar recomendaciones personalizadas para mejorar tu CV y cartas de presentación.</li>
            <li>Mejorar continuamente nuestros algoritmos de IA y la experiencia del usuario.</li>
            <li>Comunicarnos contigo respecto a actualizaciones del servicio, soporte técnico o notificaciones importantes.</li>
          </ul>
        </section>

        <section className="space-y-4">
          <h2 className="text-2xl font-bold font-heading text-white">3. Procesamiento con IA y Terceros</h2>
          <p>
            Para brindar nuestros servicios de optimización avanzada, es posible que procesemos tus datos utilizando APIs de Inteligencia Artificial provistas por terceros de confianza. Nos aseguramos de que estos socios cumplan con estrictos estándares de seguridad y confidencialidad, y que tus datos no sean utilizados para entrenar modelos públicos sin tu consentimiento explícito.
          </p>
        </section>

        <section className="space-y-4">
          <h2 className="text-2xl font-bold font-heading text-white">4. Protección de Datos</h2>
          <p>
            Implementamos medidas de seguridad técnicas, administrativas y físicas diseñadas para proteger tu información personal contra acceso, uso o divulgación no autorizados. Sin embargo, ningún sistema de transmisión por Internet o almacenamiento de datos es 100% seguro.
          </p>
        </section>

        <section className="space-y-4">
          <h2 className="text-2xl font-bold font-heading text-white">5. Tus Derechos</h2>
          <p>
            Tienes el derecho de acceder, corregir, actualizar o solicitar la eliminación de tu información personal en cualquier momento. Puedes gestionar tus preferencias de datos directamente desde la página de Configuración de tu cuenta o contactando a nuestro equipo de soporte.
          </p>
        </section>

        <section className="space-y-4">
          <h2 className="text-2xl font-bold font-heading text-white">6. Cambios a esta Política</h2>
          <p>
            Podemos actualizar estas Políticas de Privacidad periódicamente para reflejar cambios en nuestras prácticas o servicios. Te notificaremos sobre cambios significativos publicando la nueva política en nuestro sitio y, de ser necesario, a través de correo electrónico.
          </p>
        </section>

      </div>
    </div>
  );
}
