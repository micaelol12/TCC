import { Link } from 'react-router-dom'
import SharedComparison from '@8values/shared/components/ComparisonPanel'
import type { Profile } from '../../storage/localProfile'
import type { Analysis } from '../../services/analysisApi'
export default function ComparisonPanel({ profile, analysis, analysisTitle }: { profile: Profile | null; analysis: Analysis | null; analysisTitle?: string }) {
  return <SharedComparison profile={profile} analysis={analysis} analysisTitle={analysisTitle} profileAction={<Link to="/teste" className="button">Fazer meu teste</Link>} />
}
