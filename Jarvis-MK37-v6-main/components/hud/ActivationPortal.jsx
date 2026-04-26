
'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useStore } from '@/lib/store';

export default function ActivationPortal() {
  const { isActivated, activateSystem } = useStore();

  return (
    <AnimatePresence>
      {!isActivated && (
        <motion.div
          initial={{ opacity: 1 }}
          exit={{ opacity: 0, scale: 0.8 }}
          transition={{ duration: 1.5, ease: 'power3.inOut' }}
          className="absolute inset-0 flex items-center justify-center z-50"
        >
          <button 
            onClick={activateSystem}
            className="text-core-cyan border border-core-cyan px-8 py-4 rounded-full font-bold text-xl 
                       hover:bg-core-cyan hover:text-background transition-all duration-300 
                       hover:shadow-[0_0_20px_theme(colors.core.cyan)]"
          >
            INICIATE J.A.R.V.I.S.
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
