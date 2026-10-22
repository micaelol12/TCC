import { Link } from 'react-router-dom'
import SharedComparison from '@8values/shared/components/ComparisonPanel'
import type { Profile } from '../../storage/localProfile'
import type { Analysis } from '../../services/analysisApi'
export default function ComparisonPanel({ profile, analysis }: { profile: Profile | null; analysis: Analysis | null }) {
  return <SharedComparison profile={profile} analysis={analysis} profileAction={<Link to="/teste" className="button">Fazer meu teste</Link>} />
}
