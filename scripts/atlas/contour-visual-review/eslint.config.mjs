import js from '@eslint/js';
import globals from 'globals';
export default [
  { files: ['**/viewer.js'], ...js.configs.recommended, languageOptions: { globals: globals.browser } },
  { files: ['**/test_viewer.mjs'], ...js.configs.recommended, languageOptions: { globals: globals.node } },
];
