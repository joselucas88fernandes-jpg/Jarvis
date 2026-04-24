
'use client';

import { motion } from 'framer-motion';
import { useStore } from '@/lib/store';

const Ring = ({ delay, scale, amplitude, status }) => {
  const ringVariants = {
    idle: {
      rotate: 360,
      scale: [1, 1.03, 1],
      transition: {
        rotate: { repeat: Infinity, duration: 15 + delay * 5, ease: 'linear' },
        scale: { repeat: Infinity, duration: 4, ease: 'easeInOut' },
      },
    },
    speaking: {
      scale: 1 + amplitude * 0.3 + (delay * 0.05),
      transition: { type: 'spring', stiffness: 200, damping: 20 },
    },
  };

  return (
    <motion.div 
      className="absolute"
      variants={ringVariants}
      initial="idle"
      animate={status === 'SPEAKING' ? 'speaking' : 'idle'}
    >
      <svg width={scale} height={scale} viewBox="0 0 200 200">
        <circle cx="100" cy="100" r="98" stroke="rgba(0, 229, 255, 0.5)" strokeWidth="1" fill="none" />
      </svg>
    </motion.div>
  );
};

export default function CentralCore() {
  const { isActivated, systemStatus, audioAmplitude } = useStore();

  if (!isActivated) return null;

  return (
    <div className="fixed inset-0 flex items-center justify-center pointer-events-none">
      {[...Array(5)].map((_, i) => (
        <Ring 
          key={i} 
          delay={i} 
          scale={200 + i * 80}
          amplitude={audioAmplitude} 
          status={systemStatus}
        />
      ))}
    </div>
  );
}
