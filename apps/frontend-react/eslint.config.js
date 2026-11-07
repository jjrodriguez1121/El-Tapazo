import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'

export default [
  { ignores: ['dist', 'node_modules', 'coverage'] },
  {
    files: ['**/*.{js,jsx}'],
    languageOptions: {
      ecmaVersion: 'latest',
      globals: globals.browser,
      parserOptions: {
        ecmaFeatures: { jsx: true },
        sourceType: 'module',
      },
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      ...js.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
      // La regla base no ve el JSX: un componente que solo se usa como <Icono />
      // parecería sin usar. Por eso se ignoran los nombres en mayúscula, también
      // cuando llegan como prop (`{ Icono }`).
      'no-unused-vars': ['error', { varsIgnorePattern: '^[A-Z_]', argsIgnorePattern: '^[A-Z_]' }],
    },
  },
  {
    // Las ayudas de prueba mezclan componentes y funciones en un mismo archivo.
    // Nunca se montan en la aplicación, así que la recarga en caliente no aplica.
    files: ['src/pruebas/**', '**/*.test.{js,jsx}'],
    rules: { 'react-refresh/only-export-components': 'off' },
  },
]
