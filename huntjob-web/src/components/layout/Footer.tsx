import Link from "next/link";
import Image from "next/image";

export function Footer() {
  return (
    <footer className="w-full border-t border-white/5 bg-black/20 backdrop-blur-md py-8 mt-auto z-10 relative">
      <div className="container mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-6">
        
        <div className="flex items-center gap-6">
          <Link href="/terms" className="text-sm text-zinc-400 hover:text-white transition-colors">
            Términos y Condiciones
          </Link>
          <Link href="/privacy" className="text-sm text-zinc-400 hover:text-white transition-colors">
            Políticas de Privacidad
          </Link>
        </div>
        
        <div className="flex flex-col md:flex-row items-center gap-4 text-center md:text-right">
          <span className="text-xs text-zinc-500 uppercase tracking-widest font-heading font-medium">
            Powered by
          </span>
          <a 
            href="https://cumsille.tech" 
            target="_blank" 
            rel="noopener noreferrer" 
            className="opacity-70 hover:opacity-100 transition-opacity"
          >
            <img 
              src="/css-logo.png" 
              alt="Cumsille Systems Suite" 
              className="h-10 md:h-12 w-auto object-contain drop-shadow-md" 
            />
          </a>
        </div>

      </div>
    </footer>
  );
}
