import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Términos y Condiciones | HuntJob Pro",
  description: "Términos y condiciones de uso de la plataforma HuntJob Pro.",
};

export default function TermsPage() {
  return (
    <div className="container mx-auto px-4 py-20 max-w-4xl">
      <div className="space-y-8 text-zinc-300">
        <div className="text-center space-y-4 mb-16">
          <h1 className="text-4xl md:text-5xl font-bold font-heading text-transparent bg-clip-text bg-gradient-to-r from-amber-200 to-amber-500">
            Términos y Condiciones
          </h1>
          <p className="text-zinc-400">Última actualización: 24 de Julio de 2026</p>
        </div>

        <section className="space-y-4">
          <h2 className="text-2xl font-bold font-heading text-white">1. Introducción</h2>
          <p>
            Bienvenido a HuntJob Pro. Estos términos y condiciones rigen el uso de nuestra plataforma y servicios de optimización de perfil profesional e Inteligencia Artificial para la búsqueda de empleo. Al acceder y utilizar HuntJob Pro, aceptas estar sujeto a estos Términos y Condiciones.
          </p>
        </section>

        <section className="space-y-4">
          <h2 className="text-2xl font-bold font-heading text-white">2. Uso de la Plataforma</h2>
          <p>
            Nuestros servicios están diseñados para ayudarte a mejorar tu perfil profesional. Te comprometes a proporcionar información precisa, actual y completa durante el proceso de registro y uso de las herramientas de IA. El uso de cuentas automatizadas o bots para extraer información de la plataforma está estrictamente prohibido.
          </p>
        </section>

        <section className="space-y-4">
          <h2 className="text-2xl font-bold font-heading text-white">3. Generación de Contenido por IA</h2>
          <p>
            Nuestra plataforma utiliza Inteligencia Artificial avanzada para generar sugerencias de CV, cartas de presentación y análisis de mercado. Aunque nos esforzamos por ofrecer contenido de la más alta calidad, no garantizamos la exactitud absoluta de cada recomendación. Es responsabilidad del usuario revisar y validar el contenido generado antes de utilizarlo en sus postulaciones.
          </p>
        </section>

        <section className="space-y-4">
          <h2 className="text-2xl font-bold font-heading text-white">4. Privacidad y Protección de Datos</h2>
          <p>
            Tu privacidad es fundamental para nosotros. El manejo de tus datos personales, currículum vitae y preferencias laborales está regido por nuestras Políticas de Privacidad. Al utilizar HuntJob Pro, consientes el procesamiento de tus datos de acuerdo con dichas políticas.
          </p>
        </section>

        <section className="space-y-4">
          <h2 className="text-2xl font-bold font-heading text-white">5. Modificaciones de los Servicios</h2>
          <p>
            Nos reservamos el derecho de modificar, suspender o discontinuar cualquier aspecto de HuntJob Pro en cualquier momento, incluyendo la disponibilidad de características exclusivas o funcionalidades de IA, con o sin previo aviso.
          </p>
        </section>

        <section className="space-y-4">
          <h2 className="text-2xl font-bold font-heading text-white">6. Limitación de Responsabilidad</h2>
          <p>
            HuntJob Pro, sus desarrolladores (Cumsille Systems Suite) y afiliados no serán responsables de ningún daño indirecto, incidental, especial o consecuente que surja del uso o la incapacidad de usar nuestros servicios, ni del éxito o fracaso en procesos de selección laboral.
          </p>
        </section>

        <section className="space-y-4">
          <h2 className="text-2xl font-bold font-heading text-white">7. Contacto</h2>
          <p>
            Si tienes alguna pregunta sobre estos Términos y Condiciones, por favor contáctanos a través de nuestros canales oficiales de soporte.
          </p>
        </section>
      </div>
    </div>
  );
}
