/* Operator-only generated binding. Never ship in a gameplay workspace. */

export type Schema = "strata/LaunchProfile/1";
export type IsExample = boolean;
export type Version = string;
export type Digest = string;
export type ExecutablePath = string;
export type Arguments = string[];
export type WorkingDirectory = string;
export type ReviewedBootstrap = string;

export interface LaunchProfile {
  schema: Schema;
  is_example: IsExample;
  client: LaunchCommand;
  server: LaunchCommand;
}
export interface LaunchCommand {
  executable: Pin;
  executable_path: ExecutablePath;
  arguments: Arguments;
  working_directory: WorkingDirectory;
  environment: Environment;
  reviewed_bootstrap: ReviewedBootstrap;
}
export interface Pin {
  version: Version;
  digest: Digest;
}
export interface Environment {
  [k: string]: string;
}
