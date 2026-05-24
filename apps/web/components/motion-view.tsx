'use client';

import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

interface MotionViewProps {
  children: ReactNode;
  className?: string;
  delay?: number;
}

export function MotionView({ children, className, delay = 0 }: MotionViewProps) {
  return (
    <motion.div
      animate={{ opacity: 1, y: 0 }}
      className={className}
      initial={{ opacity: 0, y: 16 }}
      transition={{ duration: 0.45, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}
