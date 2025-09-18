// metro.config.js
const { getDefaultConfig } = require('expo/metro-config');
const { withNativeWind } = require('nativewind/metro');

const config = getDefaultConfig(__dirname);

// Add resolver to handle the worklets conflict
config.resolver = {
  ...config.resolver,
  alias: {
    ...config.resolver.alias,
  },
};

// Exclude problematic packages from being processed
config.resolver.blockList = [
  ...Array.from(config.resolver.blockList || []),
  /node_modules\/react-native-worklets\/.*\/node_modules\/.*/,
];

module.exports = withNativeWind(config, { input: './app/globals.css' });