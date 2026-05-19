import nextVitals from 'eslint-config-next/core-web-vitals';
import nextTypescript from 'eslint-config-next/typescript';
import rootConfig from '../../eslint.config.mjs';

export default [...rootConfig, ...nextVitals, ...nextTypescript];

