import { useEffect, useState } from 'react';

interface GoodsType {
  goods_type_id: string;
  display_name: string;
  description?: string | null;
}

interface GoodsComplianceProps {
  value: string;
  onChange: (goodsTypeId: string) => void;
}

export const GoodsCompliance = ({
  value,
  onChange,
}: GoodsComplianceProps) => {
  const [goodsTypes, setGoodsTypes] = useState<GoodsType[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadGoodsTypes() {
      setLoading(true);
      setError('');

      try {
        const response = await fetch(
          '/api/compliance/goods-types'
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(
            data.detail || 'Failed to load goods types.'
          );
        }

        setGoodsTypes(
          Array.isArray(data) ? data : []
        );
      } catch (error) {
        console.error(
          'Failed to load goods types:',
          error
        );

        if (error instanceof Error) {
          setError(error.message);
        } else {
          setError('Failed to load goods types.');
        }
      } finally {
        setLoading(false);
      }
    }

    loadGoodsTypes();
  }, []);

  const selectedGoods =
    goodsTypes.find(
      (goods) => goods.goods_type_id === value
    ) ?? null;

  return (
    <div className="flex flex-col gap-2">
      <div>
        <h4 className="text-sm font-medium text-foreground">
          What are you carrying?
        </h4>

        <p className="mt-1 text-xs text-muted-foreground">
          The load may affect the network or additional
          routing restrictions.
        </p>
      </div>

      <label
        htmlFor="goods-type"
        className="text-sm font-medium text-foreground"
      >
        Goods / Load Type
      </label>

      <select
        id="goods-type"
        value={value}
        disabled={loading}
        onChange={(event) =>
          onChange(event.target.value)
        }
        className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm text-foreground outline-none disabled:cursor-not-allowed disabled:opacity-50 focus:ring-2 focus:ring-ring"
      >
        <option value="">
          {loading
            ? 'Loading goods types...'
            : '— Select goods type —'}
        </option>

        {goodsTypes.map((goods) => (
          <option
            key={goods.goods_type_id}
            value={goods.goods_type_id}
          >
            {goods.display_name}
          </option>
        ))}
      </select>

      {error && (
        <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3">
          <p className="text-sm text-destructive">
            {error}
          </p>
        </div>
      )}
    </div>
  );
};