module.exports = {
    transform: {
      "^.+\\.(js|jsx|ts|tsx)$": "babel-jest",
    },
    transformIgnorePatterns: [
      "node_modules/(?!(<your-package>)/)", // Include specific packages
    ],
    moduleNameMapper: {
      "^@/(.*)$": "<rootDir>/src/$1", // Map paths
    },
  };