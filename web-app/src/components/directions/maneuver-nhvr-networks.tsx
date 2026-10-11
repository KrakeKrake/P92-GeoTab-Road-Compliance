import { useMemo } from 'react';

import type { NHVRNetwork } from '@/components/types';
import { Badge } from '@/components/ui/badge';
import { useNetworkAccessDetailQuery } from '@/hooks/use-network-access-detail-query';
import { useCommonStore } from '@/stores/common-store';

const STATUS_BADGE_STYLES: Record<
  NHVRNetwork['status'],
  { variant: 'outline' | 'destructive'; className?: string }
> = {
  approved: {
    variant: 'outline',
    className:
      'border-emerald-500 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
  },
  conditional: {
    variant: 'outline',
    className:
      'border-amber-500 bg-amber-500/10 text-amber-600 dark:text-amber-400',
  },
  prohibited: { variant: 'destructive' },
};

const joinNonEmpty = (parts: (string | undefined)[]) =>
  parts.filter(Boolean).join(' · ');

export function ManeuverNhvrNetworks({
  networks,
}: {
  networks: NHVRNetwork[];
}) {
  const selectedNetworks = useCommonStore(
    (state) => state.settings.nhvr_networks
  );
  const visibleNetworks = useMemo(
    () => networks.filter((network) => selectedNetworks.includes(network.name)),
    [networks, selectedNetworks]
  );

  const conditionalWayIds = useMemo(
    () => [
      ...new Set(
        visibleNetworks
          .filter((network) => network.status === 'conditional')
          .flatMap((network) => network.way_ids ?? [])
      ),
    ],
    [visibleNetworks]
  );
  const { data: detail } = useNetworkAccessDetailQuery(conditionalWayIds);

  return (
    <div className="flex flex-col gap-1">
      {visibleNetworks.map((network) => {
        const style = STATUS_BADGE_STYLES[network.status];
        const conditionTexts =
          network.status === 'conditional'
            ? [
                ...new Set(
                  (network.way_ids ?? []).flatMap((wayId) =>
                    (detail?.[String(wayId)] ?? [])
                      .filter((entry) => entry.networkName === network.name)
                      .map((entry) =>
                        joinNonEmpty([
                          entry.description || undefined,
                          entry.manager
                            ? `managed by ${entry.manager}`
                            : undefined,
                        ])
                      )
                      .filter(Boolean)
                  )
                ),
              ]
            : [];

        return (
          <div
            key={network.name}
            className="flex flex-wrap items-center gap-1.5"
          >
            <Badge variant={style.variant} className={style.className}>
              {network.name}
            </Badge>
            {conditionTexts.map((text) => (
              <span key={text} className="text-xs text-muted-foreground">
                {text}
              </span>
            ))}
          </div>
        );
      })}
    </div>
  );
}
