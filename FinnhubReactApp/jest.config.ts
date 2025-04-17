// import type { Config } from "@jest/types";
import nextJest from "next/jest";

const createJestConfig = nextJest({
  dir: "./",
});

const jestConfig = {
  preset: "ts-jest",
  testEnvironment: "jest-environment-jsdom",
  testRegex: "(/__tests__/.*|(\\.|/)(test|spec))\\.(jsx?|tsx?)$", // Add this line to include .tsx files
  transform: {
    "^.+\\.(ts|tsx)$": "ts-jest", // Explicitly handle both .ts and .tsx files
  },
  moduleNameMapper: {
    "^@/components/(.*)$": "<rootDir>/src/components/$1",
    "^@/pages/(.*)$": "<rootDir>/src/pages/$1",
    "^@/utils/(.*)$": "<rootDir>/src/utils/$1",
    "^@/hooks/(.*)$": "<rootDir>/src/hooks/$1",
    "^@/app/(.*)$": "<rootDir>/src/styles/$1",
    "\\.(css|scss)$": "<rootDir>/__mocks__/styleMock.js",
    "^react-chartjs-2$": "<rootDir>/__mocks__/react-chartjs-2.js"
  },
  setupFilesAfterEnv: ["<rootDir>/jest.setup.js"],
  // moduleDirectories: ['node_modules', '<rootDir>']
};

export default createJestConfig(jestConfig);
