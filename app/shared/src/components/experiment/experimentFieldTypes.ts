import type { ExperimentConfig, ExperimentCapabilities } from '../../domain/experimentConfig'
import type { Mode } from '../../api/analysisApi'

export type ExperimentFieldProps = {
  capabilities: ExperimentCapabilities
  config: ExperimentConfig
  mode: Mode
  busy: boolean
  onChange: (config: ExperimentConfig) => void
}
