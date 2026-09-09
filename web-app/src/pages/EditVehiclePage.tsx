import {
  useEffect,
  useState,
  type ReactNode,
} from 'react';
import { useNavigate } from '@tanstack/react-router';

interface VehicleListItem {
  profile_id: string;
  display_name: string;
  template_id: string;
  required_licence_class_id: string;
}

interface AxleConfigurationForm {
  clientId: string;
  isExisting: boolean;

  axleConfigId: string;
  displayName: string;
  maxLength: string;
  accessPath: string;
  axleGroupMassesCsv: string;

  gmlMass: string;
  cmlMass: string;
  hmlMass: string;

  note: string;
}

interface AdminVehicleData {
  category: {
    category_id: string;
    category_name: string;
  };

  template: {
    template_id: string;
    template_name: string;
    base_type: string;
  };

  profile: {
    profile_id: string;
    display_name: string;
    vehicle_family: string;
    combination_type: string;
    gvm_category: string;
    axle_count: number | '';
    axle_configurable: boolean;
    default_width_m: number;
    default_height_m: number;
    default_length_m: number;
    allow_custom_dimensions: boolean;
    required_licence_class_id: string;
  };

  dimension_rule: {
    rule_name: string;
    width_limit_m: number | '';
    height_limit_m: number | '';
    length_limit_m: number | '';
    classification_if_exceeded_limit: string;
    note: string;
  };

  input_sanity_range: {
    min_width_m: number | '';
    max_width_m: number | '';

    min_height_m: number | '';
    max_height_m: number | '';

    min_length_m: number | '';
    max_length_m: number | '';
  };

  axle_configurations: Array<{
    axle_config_id: string;
    display_name: string;
    max_length_m: number;
    access_path: string;

    axle_group_masses_csv: string;

    gml_mass_t: number | '';
    cml_mass_t: number | '';
    hml_mass_t: number | '';

    note: string;
  }>;
}

function createEmptyAxleConfiguration(): AxleConfigurationForm {
  return {
    clientId: `${Date.now()}-${Math.random()}`,
    isExisting: false,

    axleConfigId: '',
    displayName: '',
    maxLength: '',
    accessPath: 'general_access',
    axleGroupMassesCsv: '',

    gmlMass: '',
    cmlMass: '',
    hmlMass: '',

    note: '',
  };
}

function stringValue(
  value: string | number | null | undefined
) {
  if (
    value === null ||
    value === undefined ||
    value === ''
  ) {
    return '';
  }

  return String(value);
}

const EditVehiclePage = () => {
  const navigate = useNavigate();

  // =========================================================
  // Vehicle selector
  // =========================================================

  const [vehicles, setVehicles] = useState<
    VehicleListItem[]
  >([]);

  const [selectedProfileId, setSelectedProfileId] =
    useState('');

  const [vehicleListLoading, setVehicleListLoading] =
    useState(true);

  const [vehicleLoading, setVehicleLoading] =
    useState(false);

  // =========================================================
  // Category
  // =========================================================

  const [categoryId, setCategoryId] = useState('');
  const [categoryName, setCategoryName] = useState('');

  // =========================================================
  // Template
  // =========================================================

  const [templateId, setTemplateId] = useState('');
  const [templateName, setTemplateName] = useState('');
  const [baseType, setBaseType] = useState('');

  // =========================================================
  // Profile
  // =========================================================

  const [profileId, setProfileId] = useState('');
  const [displayName, setDisplayName] = useState('');

  const [vehicleFamily, setVehicleFamily] = useState('');
  const [combinationType, setCombinationType] =
    useState('');

  const [gvmCategory, setGvmCategory] = useState('');

  const [axleCount, setAxleCount] = useState('');

  const [axleConfigurable, setAxleConfigurable] =
    useState(true);

  const [
    allowCustomDimensions,
    setAllowCustomDimensions,
  ] = useState(true);

  const [requiredLicence, setRequiredLicence] =
    useState('');

  // =========================================================
  // Default dimensions
  // =========================================================

  const [defaultWidth, setDefaultWidth] = useState('');
  const [defaultHeight, setDefaultHeight] =
    useState('');
  const [defaultLength, setDefaultLength] =
    useState('');

  // =========================================================
  // Dimension rule
  // =========================================================

  const [ruleName, setRuleName] = useState('');

  const [widthLimit, setWidthLimit] = useState('');
  const [heightLimit, setHeightLimit] = useState('');
  const [lengthLimit, setLengthLimit] = useState('');

  const [
    classificationIfExceeded,
    setClassificationIfExceeded,
  ] = useState('class_3');

  const [ruleNote, setRuleNote] = useState('');

  // =========================================================
  // Sanity ranges
  // =========================================================

  const [minWidth, setMinWidth] = useState('');
  const [maxWidth, setMaxWidth] = useState('');

  const [minHeight, setMinHeight] = useState('');
  const [maxHeight, setMaxHeight] = useState('');

  const [minLength, setMinLength] = useState('');
  const [maxLength, setMaxLength] = useState('');

  // =========================================================
  // Axle configurations
  // =========================================================

  const [
    axleConfigurations,
    setAxleConfigurations,
  ] = useState<AxleConfigurationForm[]>([]);

  // =========================================================
  // Status
  // =========================================================

  const [saving, setSaving] = useState(false);

  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] =
    useState('');

  // =========================================================
  // Load vehicle list
  // =========================================================

  useEffect(() => {
    async function loadVehicles() {
      setVehicleListLoading(true);
      setError('');

      try {
        const response = await fetch(
          '/api/compliance/admin/vehicles'
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(
            data.detail ||
              'Failed to load vehicle list.'
          );
        }

        setVehicles(
          Array.isArray(data) ? data : []
        );
      } catch (error) {
        console.error(
          'Failed to load vehicles:',
          error
        );

        if (error instanceof Error) {
          setError(error.message);
        } else {
          setError(
            'Failed to load vehicle list.'
          );
        }
      } finally {
        setVehicleListLoading(false);
      }
    }

    loadVehicles();
  }, []);

  // =========================================================
  // Load selected vehicle
  // =========================================================

  useEffect(() => {
    async function loadVehicle() {
      setError('');
      setSuccessMessage('');

      if (!selectedProfileId) {
        clearVehicleForm();
        return;
      }

      setVehicleLoading(true);

      try {
        const response = await fetch(
          `/api/compliance/admin/vehicles/${selectedProfileId}`
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(
            data.detail ||
              'Failed to load vehicle.'
          );
        }

        populateVehicleForm(
          data as AdminVehicleData
        );
      } catch (error) {
        console.error(
          'Failed to load vehicle:',
          error
        );

        if (error instanceof Error) {
          setError(error.message);
        } else {
          setError(
            'Failed to load vehicle.'
          );
        }
      } finally {
        setVehicleLoading(false);
      }
    }

    loadVehicle();
  }, [selectedProfileId]);

  // =========================================================
  // Populate form
  // =========================================================

  function populateVehicleForm(
    data: AdminVehicleData
  ) {
    setCategoryId(
      data.category.category_id ?? ''
    );

    setCategoryName(
      data.category.category_name ?? ''
    );

    setTemplateId(
      data.template.template_id ?? ''
    );

    setTemplateName(
      data.template.template_name ?? ''
    );

    setBaseType(
      data.template.base_type ?? ''
    );

    setProfileId(
      data.profile.profile_id ?? ''
    );

    setDisplayName(
      data.profile.display_name ?? ''
    );

    setVehicleFamily(
      data.profile.vehicle_family ?? ''
    );

    setCombinationType(
      data.profile.combination_type ?? ''
    );

    setGvmCategory(
      data.profile.gvm_category ?? ''
    );

    setAxleCount(
      stringValue(data.profile.axle_count)
    );

    setAxleConfigurable(
      data.profile.axle_configurable
    );

    setDefaultWidth(
      stringValue(
        data.profile.default_width_m
      )
    );

    setDefaultHeight(
      stringValue(
        data.profile.default_height_m
      )
    );

    setDefaultLength(
      stringValue(
        data.profile.default_length_m
      )
    );

    setAllowCustomDimensions(
      data.profile.allow_custom_dimensions
    );

    setRequiredLicence(
      data.profile.required_licence_class_id ??
        ''
    );

    setRuleName(
      data.dimension_rule.rule_name ?? ''
    );

    setWidthLimit(
      stringValue(
        data.dimension_rule.width_limit_m
      )
    );

    setHeightLimit(
      stringValue(
        data.dimension_rule.height_limit_m
      )
    );

    setLengthLimit(
      stringValue(
        data.dimension_rule.length_limit_m
      )
    );

    setClassificationIfExceeded(
      data.dimension_rule
        .classification_if_exceeded_limit ||
        'class_3'
    );

    setRuleNote(
      data.dimension_rule.note ?? ''
    );

    setMinWidth(
      stringValue(
        data.input_sanity_range.min_width_m
      )
    );

    setMaxWidth(
      stringValue(
        data.input_sanity_range.max_width_m
      )
    );

    setMinHeight(
      stringValue(
        data.input_sanity_range.min_height_m
      )
    );

    setMaxHeight(
      stringValue(
        data.input_sanity_range.max_height_m
      )
    );

    setMinLength(
      stringValue(
        data.input_sanity_range.min_length_m
      )
    );

    setMaxLength(
      stringValue(
        data.input_sanity_range.max_length_m
      )
    );

    setAxleConfigurations(
      data.axle_configurations.map(
        (configuration) => ({
          clientId: `existing-${configuration.axle_config_id}`,
          isExisting: true,

          axleConfigId:
            configuration.axle_config_id,

          displayName:
            configuration.display_name,

          maxLength: stringValue(
            configuration.max_length_m
          ),

          accessPath:
            configuration.access_path,

          axleGroupMassesCsv:
            configuration.axle_group_masses_csv,

          gmlMass: stringValue(
            configuration.gml_mass_t
          ),

          cmlMass: stringValue(
            configuration.cml_mass_t
          ),

          hmlMass: stringValue(
            configuration.hml_mass_t
          ),

          note: configuration.note ?? '',
        })
      )
    );
  }

  // =========================================================
  // Clear form
  // =========================================================

  function clearVehicleForm() {
    setCategoryId('');
    setCategoryName('');

    setTemplateId('');
    setTemplateName('');
    setBaseType('');

    setProfileId('');
    setDisplayName('');

    setVehicleFamily('');
    setCombinationType('');
    setGvmCategory('');

    setAxleCount('');
    setAxleConfigurable(true);

    setDefaultWidth('');
    setDefaultHeight('');
    setDefaultLength('');

    setAllowCustomDimensions(true);
    setRequiredLicence('');

    setRuleName('');

    setWidthLimit('');
    setHeightLimit('');
    setLengthLimit('');

    setClassificationIfExceeded(
      'class_3'
    );

    setRuleNote('');

    setMinWidth('');
    setMaxWidth('');

    setMinHeight('');
    setMaxHeight('');

    setMinLength('');
    setMaxLength('');

    setAxleConfigurations([]);
  }

  // =========================================================
  // Axle helpers
  // =========================================================

  function updateAxleConfiguration(
    clientId: string,
    field: keyof AxleConfigurationForm,
    value: string
  ) {
    setAxleConfigurations((current) =>
      current.map((configuration) =>
        configuration.clientId === clientId
          ? {
              ...configuration,
              [field]: value,
            }
          : configuration
      )
    );

    setError('');
    setSuccessMessage('');
  }

  function addAxleConfiguration() {
    setAxleConfigurations((current) => [
      ...current,
      createEmptyAxleConfiguration(),
    ]);
  }

  function removeNewAxleConfiguration(
    clientId: string
  ) {
    setAxleConfigurations((current) =>
      current.filter(
        (configuration) =>
          configuration.clientId !== clientId
      )
    );
  }

  function parseAxleGroupMasses(
    value: string
  ) {
    if (!value.trim()) {
      return [];
    }

    return value
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean)
      .map(Number);
  }

  function numberOrNull(value: string) {
    if (value.trim() === '') {
      return null;
    }

    return Number(value);
  }

  // =========================================================
  // Validation
  // =========================================================

  function validateForm(): string | null {
    if (!selectedProfileId) {
      return 'Please select a vehicle first.';
    }

    if (!categoryName.trim()) {
      return 'Category name is required.';
    }

    if (!templateName.trim()) {
      return 'Template name is required.';
    }

    if (!baseType) {
      return 'Base type is required.';
    }

    if (!displayName.trim()) {
      return 'Vehicle display name is required.';
    }

    if (!vehicleFamily) {
      return 'Vehicle family is required.';
    }

    if (!combinationType) {
      return 'Combination type is required.';
    }

    if (!requiredLicence) {
      return 'Required licence class is required.';
    }

    if (
      defaultWidth === '' ||
      defaultHeight === '' ||
      defaultLength === ''
    ) {
      return 'All default dimensions are required.';
    }

    if (
      widthLimit === '' ||
      heightLimit === '' ||
      lengthLimit === ''
    ) {
      return 'All legal dimension limits are required.';
    }

    if (
      minWidth === '' ||
      maxWidth === '' ||
      minHeight === '' ||
      maxHeight === '' ||
      minLength === '' ||
      maxLength === ''
    ) {
      return 'All input sanity ranges are required.';
    }

    const minW = Number(minWidth);
    const maxW = Number(maxWidth);

    const minH = Number(minHeight);
    const maxH = Number(maxHeight);

    const minL = Number(minLength);
    const maxL = Number(maxLength);

    if (minW > maxW) {
      return 'Minimum width cannot be greater than maximum width.';
    }

    if (minH > maxH) {
      return 'Minimum height cannot be greater than maximum height.';
    }

    if (minL > maxL) {
      return 'Minimum length cannot be greater than maximum length.';
    }

    if (
      Number(defaultWidth) < minW ||
      Number(defaultWidth) > maxW
    ) {
      return 'Default width must be inside the sanity range.';
    }

    if (
      Number(defaultHeight) < minH ||
      Number(defaultHeight) > maxH
    ) {
      return 'Default height must be inside the sanity range.';
    }

    if (
      Number(defaultLength) < minL ||
      Number(defaultLength) > maxL
    ) {
      return 'Default length must be inside the sanity range.';
    }

    if (Number(widthLimit) > maxW) {
      return 'Legal width limit cannot exceed maximum sanity width.';
    }

    if (Number(heightLimit) > maxH) {
      return 'Legal height limit cannot exceed maximum sanity height.';
    }

    if (Number(lengthLimit) > maxL) {
      return 'Legal length limit cannot exceed maximum sanity length.';
    }

    if (
      axleConfigurable &&
      axleConfigurations.length === 0
    ) {
      return 'At least one axle configuration is required.';
    }

    const seenAxleIds = new Set<string>();

    for (
      let index = 0;
      index < axleConfigurations.length;
      index++
    ) {
      const configuration =
        axleConfigurations[index];

      if (!configuration) {
        continue;
      }

      const position = index + 1;

      if (
        !configuration.axleConfigId.trim()
      ) {
        return `Configuration ${position}: axle configuration ID is required.`;
      }

      const normalisedId =
        configuration.axleConfigId
          .trim()
          .toUpperCase();

      if (seenAxleIds.has(normalisedId)) {
        return `Duplicate axle configuration ID: ${normalisedId}`;
      }

      seenAxleIds.add(normalisedId);

      if (
        !configuration.displayName.trim()
      ) {
        return `Configuration ${position}: display name is required.`;
      }

      const maxAxleLength = Number(
        configuration.maxLength
      );

      if (
        !Number.isFinite(maxAxleLength) ||
        maxAxleLength <= 0
      ) {
        return `Configuration ${position}: maximum length must be greater than zero.`;
      }

      if (
        maxAxleLength < minL ||
        maxAxleLength > maxL
      ) {
        return `Configuration ${position}: maximum length must be between ${minL} m and ${maxL} m.`;
      }

      if (!configuration.accessPath) {
        return `Configuration ${position}: access path is required.`;
      }

      const groupMasses =
        parseAxleGroupMasses(
          configuration.axleGroupMassesCsv
        );

      if (groupMasses.length === 0) {
        return `Configuration ${position}: at least one axle group mass is required.`;
      }

      if (
        groupMasses.some(
          (mass) =>
            !Number.isFinite(mass) ||
            mass < 0
        )
      ) {
        return `Configuration ${position}: axle group masses must be valid non-negative numbers.`;
      }

      for (const [
        label,
        value,
      ] of [
        ['GML', configuration.gmlMass],
        ['CML', configuration.cmlMass],
        ['HML', configuration.hmlMass],
      ]) {
        if (
          value !== '' &&
          (!Number.isFinite(Number(value)) ||
            Number(value) < 0)
        ) {
          return `Configuration ${position}: ${label} mass must be zero or greater.`;
        }
      }
    }

    return null;
  }

  // =========================================================
  // Save
  // =========================================================

  async function updateVehicle() {
    setError('');
    setSuccessMessage('');

    const validationError =
      validateForm();

    if (validationError) {
      setError(validationError);

      window.scrollTo({
        top: 0,
        behavior: 'smooth',
      });

      return;
    }

    setSaving(true);

    try {
      const payload = {
        category: {
          category_id: categoryId,
          category_name: categoryName,
        },

        template: {
          template_id: templateId,
          template_name: templateName,
          base_type: baseType,
        },

        profile: {
          profile_id: profileId,

          display_name: displayName,

          vehicle_family: vehicleFamily,

          combination_type:
            combinationType,

          gvm_category:
            gvmCategory || null,

          axle_count:
            axleCount === ''
              ? null
              : Number(axleCount),

          axle_configurable:
            axleConfigurable,

          default_width_m:
            Number(defaultWidth),

          default_height_m:
            Number(defaultHeight),

          default_length_m:
            Number(defaultLength),

          allow_custom_dimensions:
            allowCustomDimensions,

          required_licence_class_id:
            requiredLicence,
        },

        dimension_rule: {
          rule_name: ruleName,

          width_limit_m:
            Number(widthLimit),

          height_limit_m:
            Number(heightLimit),

          length_limit_m:
            Number(lengthLimit),

          classification_if_exceeded_limit:
            classificationIfExceeded,

          note: ruleNote,
        },

        input_sanity_range: {
          min_width_m:
            Number(minWidth),

          max_width_m:
            Number(maxWidth),

          min_height_m:
            Number(minHeight),

          max_height_m:
            Number(maxHeight),

          min_length_m:
            Number(minLength),

          max_length_m:
            Number(maxLength),
        },

        axle_configurations:
          axleConfigurable
            ? axleConfigurations.map(
                (configuration) => ({
                  axle_config_id:
                    configuration.axleConfigId,

                  display_name:
                    configuration.displayName,

                  max_length_m:
                    Number(
                      configuration.maxLength
                    ),

                  access_path:
                    configuration.accessPath,

                  axle_group_masses_t:
                    parseAxleGroupMasses(
                      configuration.axleGroupMassesCsv
                    ),

                  gml_mass_t:
                    numberOrNull(
                      configuration.gmlMass
                    ),

                  cml_mass_t:
                    numberOrNull(
                      configuration.cmlMass
                    ),

                  hml_mass_t:
                    numberOrNull(
                      configuration.hmlMass
                    ),

                  note:
                    configuration.note,
                })
              )
            : [],
      };

      console.log(
        'Update vehicle payload:',
        payload
      );

      const response = await fetch(
        `/api/compliance/admin/vehicles/${selectedProfileId}`,
        {
          method: 'PUT',

          headers: {
            'Content-Type':
              'application/json',
          },

          body: JSON.stringify(payload),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            'Failed to update vehicle.'
        );
      }

      setSuccessMessage(
        'Vehicle updated successfully.'
      );

      /*
       * Reload vehicle data so the page reflects
       * exactly what is now stored in the DB.
       */
      const reloadResponse = await fetch(
        `/api/compliance/admin/vehicles/${selectedProfileId}`
      );

      if (reloadResponse.ok) {
        const reloadedData =
          await reloadResponse.json();

        populateVehicleForm(
          reloadedData as AdminVehicleData
        );
      }

      /*
       * Reload the vehicle list as the display name
       * might have changed.
       */
      const listResponse = await fetch(
        '/api/compliance/admin/vehicles'
      );

      if (listResponse.ok) {
        const listData =
          await listResponse.json();

        setVehicles(
          Array.isArray(listData)
            ? listData
            : []
        );
      }

      window.scrollTo({
        top: 0,
        behavior: 'smooth',
      });
    } catch (error) {
      console.error(
        'Failed to update vehicle:',
        error
      );

      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError(
          'Failed to update vehicle.'
        );
      }

      window.scrollTo({
        top: 0,
        behavior: 'smooth',
      });
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="min-h-screen bg-background p-6">
      <div className="mx-auto w-full max-w-4xl">

        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">
              HeavyRoute
            </h2>

            <p className="text-sm text-muted-foreground">
              Heavy Vehicle Compliance System
            </p>
          </div>

          <button
            type="button"
            onClick={() =>
              navigate({ to: '/' })
            }
            className="rounded-md border border-border px-4 py-2 text-sm font-medium hover:bg-accent"
          >
            Back to Map
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 rounded-md border border-destructive/30 bg-destructive/10 p-4">
            <p className="text-sm font-semibold text-destructive">
              Unable to update vehicle
            </p>

            <p className="mt-1 text-sm text-destructive">
              {error}
            </p>
          </div>
        )}

        {/* Success */}
        {successMessage && (
          <div className="mb-6 rounded-md border border-green-500/30 bg-green-500/10 p-4">
            <p className="text-sm font-semibold">
              Vehicle Updated
            </p>

            <p className="mt-1 text-sm text-muted-foreground">
              {successMessage}
            </p>
          </div>
        )}

        {/* Vehicle selector */}
        <section className="mb-6 rounded-lg border border-border bg-card p-6 shadow-sm">
          <h1 className="text-2xl font-semibold">
            Edit Vehicle Type
          </h1>

          <p className="mt-2 text-sm text-muted-foreground">
            Select an existing vehicle profile to
            modify its compliance configuration.
          </p>

          <div className="mt-5">
            <Field label="Vehicle">
              <select
                value={selectedProfileId}
                onChange={(event) =>
                  setSelectedProfileId(
                    event.target.value
                  )
                }
                disabled={vehicleListLoading}
                className={inputClass}
              >
                <option value="">
                  {vehicleListLoading
                    ? 'Loading vehicles...'
                    : '— Select vehicle —'}
                </option>

                {vehicles.map((vehicle) => (
                  <option
                    key={vehicle.profile_id}
                    value={vehicle.profile_id}
                  >
                    {vehicle.display_name} —{' '}
                    {vehicle.profile_id}
                  </option>
                ))}
              </select>
            </Field>
          </div>
        </section>

        {vehicleLoading && (
          <div className="rounded-md bg-muted p-4 text-sm text-muted-foreground">
            Loading vehicle information...
          </div>
        )}

        {!vehicleLoading &&
          selectedProfileId &&
          profileId && (
            <section className="rounded-lg border border-border bg-card p-6 shadow-sm">

              <div className="flex flex-col gap-8">

                {/* 1 Category */}
                <section>
                  <SectionTitle
                    number="1"
                    title="Vehicle Category"
                    description="The category ID cannot be changed for an existing vehicle."
                  />

                  <div className="grid gap-4 md:grid-cols-2">
                    <Field label="Category ID">
                      <input
                        value={categoryId}
                        readOnly
                        className={`${inputClass} bg-muted text-muted-foreground`}
                      />
                    </Field>

                    <Field label="Category Name">
                      <input
                        value={categoryName}
                        onChange={(event) =>
                          setCategoryName(
                            event.target.value
                          )
                        }
                        className={inputClass}
                      />
                    </Field>
                  </div>
                </section>

                <Divider />

                {/* 2 Template */}
                <section>
                  <SectionTitle
                    number="2"
                    title="Vehicle Template"
                    description="Template ID cannot be changed on the edit page."
                  />

                  <div className="grid gap-4 md:grid-cols-2">
                    <Field label="Template ID">
                      <input
                        value={templateId}
                        readOnly
                        className={`${inputClass} bg-muted text-muted-foreground`}
                      />
                    </Field>

                    <Field label="Template Name">
                      <input
                        value={templateName}
                        onChange={(event) =>
                          setTemplateName(
                            event.target.value
                          )
                        }
                        className={inputClass}
                      />
                    </Field>

                    <Field label="Base Type">
                      <select
                        value={baseType}
                        onChange={(event) =>
                          setBaseType(
                            event.target.value
                          )
                        }
                        className={inputClass}
                      >
                        <option value="rigid">
                          Rigid
                        </option>

                        <option value="articulated">
                          Articulated
                        </option>

                        <option value="b_double">
                          B-Double / Multi Combination
                        </option>
                      </select>
                    </Field>
                  </div>
                </section>

                <Divider />

                {/* 3 Profile */}
                <section>
                  <SectionTitle
                    number="3"
                    title="Vehicle Profile"
                    description="Update vehicle properties and licence requirements."
                  />

                  <div className="grid gap-4 md:grid-cols-2">
                    <Field
                      label="Profile ID"
                      help="Profile ID cannot be changed. Create a new vehicle if a new ID is required."
                    >
                      <input
                        value={profileId}
                        readOnly
                        className={`${inputClass} bg-muted text-muted-foreground`}
                      />
                    </Field>

                    <Field label="Display Name">
                      <input
                        value={displayName}
                        onChange={(event) =>
                          setDisplayName(
                            event.target.value
                          )
                        }
                        className={inputClass}
                      />
                    </Field>

                    <Field label="Vehicle Family">
                      <select
                        value={vehicleFamily}
                        onChange={(event) =>
                          setVehicleFamily(
                            event.target.value
                          )
                        }
                        className={inputClass}
                      >
                        <option value="rigid_truck">
                          Rigid Truck
                        </option>

                        <option value="articulated">
                          Articulated
                        </option>

                        <option value="multi_combination">
                          Multi Combination
                        </option>
                      </select>
                    </Field>

                    <Field label="Combination Type">
                      <select
                        value={combinationType}
                        onChange={(event) =>
                          setCombinationType(
                            event.target.value
                          )
                        }
                        className={inputClass}
                      >
                        <option value="single_vehicle">
                          Single Vehicle
                        </option>

                        <option value="single_trailer">
                          Single Trailer
                        </option>

                        <option value="multi_trailer">
                          Multi Trailer
                        </option>
                      </select>
                    </Field>

                    <Field label="GVM Category">
                      <select
                        value={gvmCategory}
                        onChange={(event) =>
                          setGvmCategory(
                            event.target.value
                          )
                        }
                        className={inputClass}
                      >
                        <option value="">
                          — Not applicable —
                        </option>

                        <option value="light">
                          Light
                        </option>

                        <option value="medium">
                          Medium
                        </option>

                        <option value="heavy">
                          Heavy
                        </option>

                        <option value="heavy_combination">
                          Heavy Combination
                        </option>

                        <option value="multi_combination">
                          Multi Combination
                        </option>
                      </select>
                    </Field>

                    <Field label="Required Licence Class">
                      <select
                        value={requiredLicence}
                        onChange={(event) =>
                          setRequiredLicence(
                            event.target.value
                          )
                        }
                        className={inputClass}
                      >
                        <option value="LR">
                          LR — Light Rigid
                        </option>

                        <option value="MR">
                          MR — Medium Rigid
                        </option>

                        <option value="HR">
                          HR — Heavy Rigid
                        </option>

                        <option value="HC">
                          HC — Heavy Combination
                        </option>

                        <option value="MC">
                          MC — Multi Combination
                        </option>
                      </select>
                    </Field>

                    <Field
                      label="Axle Count"
                      help="Leave blank when the axle count varies by configuration."
                    >
                      <input
                        type="number"
                        min="1"
                        step="1"
                        value={axleCount}
                        onChange={(event) =>
                          setAxleCount(
                            event.target.value
                          )
                        }
                        className={inputClass}
                      />
                    </Field>
                  </div>

                  <div className="mt-5 flex flex-col gap-3">
                    <label className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={axleConfigurable}
                        onChange={(event) =>
                          setAxleConfigurable(
                            event.target.checked
                          )
                        }
                        className="h-4 w-4"
                      />

                      <span className="text-sm">
                        Vehicle has selectable axle
                        configurations
                      </span>
                    </label>

                    <label className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={
                          allowCustomDimensions
                        }
                        onChange={(event) =>
                          setAllowCustomDimensions(
                            event.target.checked
                          )
                        }
                        className="h-4 w-4"
                      />

                      <span className="text-sm">
                        Allow users to enter custom
                        dimensions
                      </span>
                    </label>
                  </div>
                </section>

                <Divider />

                {/* 4 Defaults */}
                <section>
                  <SectionTitle
                    number="4"
                    title="Default Dimensions"
                    description="Update the default vehicle dimensions."
                  />

                  <div className="grid gap-4 md:grid-cols-3">
                    <MeasurementField
                      label="Width"
                      value={defaultWidth}
                      onChange={setDefaultWidth}
                    />

                    <MeasurementField
                      label="Height"
                      value={defaultHeight}
                      onChange={setDefaultHeight}
                    />

                    <MeasurementField
                      label="Length"
                      value={defaultLength}
                      onChange={setDefaultLength}
                    />
                  </div>
                </section>

                <Divider />

                {/* 5 Rule */}
                <section>
                  <SectionTitle
                    number="5"
                    title="Dimension Rule"
                    description="Update the legal dimension classification limits."
                  />

                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="md:col-span-2">
                      <Field label="Rule Name">
                        <input
                          value={ruleName}
                          onChange={(event) =>
                            setRuleName(
                              event.target.value
                            )
                          }
                          className={inputClass}
                        />
                      </Field>
                    </div>

                    <MeasurementField
                      label="Legal Width Limit"
                      value={widthLimit}
                      onChange={setWidthLimit}
                    />

                    <MeasurementField
                      label="Legal Height Limit"
                      value={heightLimit}
                      onChange={setHeightLimit}
                    />

                    <MeasurementField
                      label="Legal Length Limit"
                      value={lengthLimit}
                      onChange={setLengthLimit}
                    />

                    <Field label="Classification if Limit Exceeded">
                      <select
                        value={
                          classificationIfExceeded
                        }
                        onChange={(event) =>
                          setClassificationIfExceeded(
                            event.target.value
                          )
                        }
                        className={inputClass}
                      >
                        <option value="general_access">
                          General Access
                        </option>

                        <option value="class_1">
                          Class 1
                        </option>

                        <option value="class_2">
                          Class 2
                        </option>

                        <option value="class_3">
                          Class 3
                        </option>
                      </select>
                    </Field>

                    <div className="md:col-span-2">
                      <Field label="Rule Note">
                        <textarea
                          value={ruleNote}
                          onChange={(event) =>
                            setRuleNote(
                              event.target.value
                            )
                          }
                          rows={3}
                          className="w-full resize-y rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
                        />
                      </Field>
                    </div>
                  </div>
                </section>

                <Divider />

                {/* 6 Sanity */}
                <section>
                  <SectionTitle
                    number="6"
                    title="Input Sanity Range"
                    description="Update acceptable custom dimension ranges."
                  />

                  <div className="overflow-hidden rounded-md border border-border">
                    <div className="grid grid-cols-3 gap-3 bg-muted px-4 py-3 text-sm font-medium">
                      <span>Dimension</span>
                      <span>Minimum</span>
                      <span>Maximum</span>
                    </div>

                    <SanityRangeRow
                      label="Width"
                      minimum={minWidth}
                      maximum={maxWidth}
                      onMinimumChange={
                        setMinWidth
                      }
                      onMaximumChange={
                        setMaxWidth
                      }
                    />

                    <SanityRangeRow
                      label="Height"
                      minimum={minHeight}
                      maximum={maxHeight}
                      onMinimumChange={
                        setMinHeight
                      }
                      onMaximumChange={
                        setMaxHeight
                      }
                    />

                    <SanityRangeRow
                      label="Length"
                      minimum={minLength}
                      maximum={maxLength}
                      onMinimumChange={
                        setMinLength
                      }
                      onMaximumChange={
                        setMaxLength
                      }
                    />
                  </div>
                </section>

                <Divider />

                {/* 7 Axles */}
                <section>
                  <div className="mb-5 flex items-start justify-between gap-4">
                    <div>
                      <h3 className="text-base font-semibold">
                        7. Axle Configurations
                      </h3>

                      <p className="mt-1 text-sm text-muted-foreground">
                        Edit existing configurations or
                        add additional ones.
                      </p>
                    </div>

                    {axleConfigurable && (
                      <button
                        type="button"
                        onClick={
                          addAxleConfiguration
                        }
                        className="shrink-0 rounded-md border border-border px-3 py-2 text-sm font-medium hover:bg-accent"
                      >
                        + Add Configuration
                      </button>
                    )}
                  </div>

                  {axleConfigurable && (
                    <div className="mb-4 rounded-md bg-muted p-3 text-xs text-muted-foreground">
                      Existing axle configurations can
                      be edited. The current backend does
                      not yet support deleting an existing
                      configuration from this page.
                    </div>
                  )}

                  {axleConfigurable && (
                    <div className="flex flex-col gap-5">
                      {axleConfigurations.map(
                        (
                          configuration,
                          index
                        ) => (
                          <div
                            key={
                              configuration.clientId
                            }
                            className="rounded-lg border border-border p-5"
                          >
                            <div className="mb-5 flex items-center justify-between">
                              <h4 className="font-semibold">
                                Configuration{' '}
                                {index + 1}
                              </h4>

                              {!configuration.isExisting && (
                                <button
                                  type="button"
                                  onClick={() =>
                                    removeNewAxleConfiguration(
                                      configuration.clientId
                                    )
                                  }
                                  className="text-sm font-medium text-destructive hover:underline"
                                >
                                  Remove
                                </button>
                              )}
                            </div>

                            <div className="grid gap-4 md:grid-cols-2">
                              <Field
                                label="Axle Configuration ID"
                                help={
                                  configuration.isExisting
                                    ? 'Existing axle configuration IDs should not be changed.'
                                    : undefined
                                }
                              >
                                <input
                                  value={
                                    configuration.axleConfigId
                                  }
                                  readOnly={
                                    configuration.isExisting
                                  }
                                  onChange={(event) =>
                                    updateAxleConfiguration(
                                      configuration.clientId,
                                      'axleConfigId',
                                      event.target.value.toUpperCase()
                                    )
                                  }
                                  className={`${inputClass} ${
                                    configuration.isExisting
                                      ? 'bg-muted text-muted-foreground'
                                      : ''
                                  }`}
                                />
                              </Field>

                              <Field label="Display Name">
                                <input
                                  value={
                                    configuration.displayName
                                  }
                                  onChange={(event) =>
                                    updateAxleConfiguration(
                                      configuration.clientId,
                                      'displayName',
                                      event.target.value
                                    )
                                  }
                                  className={
                                    inputClass
                                  }
                                />
                              </Field>

                              <MeasurementField
                                label="Maximum Length"
                                value={
                                  configuration.maxLength
                                }
                                onChange={(
                                  value
                                ) =>
                                  updateAxleConfiguration(
                                    configuration.clientId,
                                    'maxLength',
                                    value
                                  )
                                }
                              />

                              <Field label="Access Path">
                                <select
                                  value={
                                    configuration.accessPath
                                  }
                                  onChange={(event) =>
                                    updateAxleConfiguration(
                                      configuration.clientId,
                                      'accessPath',
                                      event.target.value
                                    )
                                  }
                                  className={
                                    inputClass
                                  }
                                >
                                  <option value="general_access">
                                    General Access
                                  </option>

                                  <option value="class_1">
                                    Class 1
                                  </option>

                                  <option value="class_2">
                                    Class 2
                                  </option>

                                  <option value="class_3">
                                    Class 3
                                  </option>
                                </select>
                              </Field>

                              <div className="md:col-span-2">
                                <Field
                                  label="Axle Group Masses"
                                  help="Enter masses in order separated by commas."
                                >
                                  <input
                                    value={
                                      configuration.axleGroupMassesCsv
                                    }
                                    onChange={(event) =>
                                      updateAxleConfiguration(
                                        configuration.clientId,
                                        'axleGroupMassesCsv',
                                        event.target.value
                                      )
                                    }
                                    className={
                                      inputClass
                                    }
                                  />
                                </Field>
                              </div>
                            </div>

                            <div className="mt-5">
                              <h5 className="mb-3 text-sm font-semibold">
                                Mass Limits
                              </h5>

                              <div className="grid gap-4 md:grid-cols-3">
                                <MassField
                                  label="GML"
                                  value={
                                    configuration.gmlMass
                                  }
                                  onChange={(
                                    value
                                  ) =>
                                    updateAxleConfiguration(
                                      configuration.clientId,
                                      'gmlMass',
                                      value
                                    )
                                  }
                                />

                                <MassField
                                  label="CML"
                                  value={
                                    configuration.cmlMass
                                  }
                                  onChange={(
                                    value
                                  ) =>
                                    updateAxleConfiguration(
                                      configuration.clientId,
                                      'cmlMass',
                                      value
                                    )
                                  }
                                />

                                <MassField
                                  label="HML"
                                  value={
                                    configuration.hmlMass
                                  }
                                  onChange={(
                                    value
                                  ) =>
                                    updateAxleConfiguration(
                                      configuration.clientId,
                                      'hmlMass',
                                      value
                                    )
                                  }
                                />
                              </div>
                            </div>

                            <div className="mt-5">
                              <Field label="Configuration Note">
                                <textarea
                                  value={
                                    configuration.note
                                  }
                                  onChange={(event) =>
                                    updateAxleConfiguration(
                                      configuration.clientId,
                                      'note',
                                      event.target.value
                                    )
                                  }
                                  rows={2}
                                  className="w-full resize-y rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
                                />
                              </Field>
                            </div>
                          </div>
                        )
                      )}
                    </div>
                  )}
                </section>

                <Divider />

                {/* Save */}
                <div className="flex justify-end gap-3">
                  <button
                    type="button"
                    onClick={() =>
                      navigate({ to: '/' })
                    }
                    disabled={saving}
                    className="h-10 rounded-md border border-border px-5 text-sm font-medium hover:bg-accent disabled:opacity-50"
                  >
                    Cancel
                  </button>

                  <button
                    type="button"
                    onClick={updateVehicle}
                    disabled={saving}
                    className="h-10 rounded-md bg-primary px-6 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {saving
                      ? 'Saving Changes...'
                      : 'Save Changes'}
                  </button>
                </div>
              </div>
            </section>
          )}
      </div>
    </main>
  );
};

export default EditVehiclePage;

// =========================================================
// Shared helper components
// =========================================================

const inputClass =
  'h-10 w-full rounded-md border border-input bg-background px-3 text-sm text-foreground outline-none focus:ring-2 focus:ring-ring';

function Divider() {
  return (
    <div className="border-t border-border" />
  );
}

function SectionTitle({
  number,
  title,
  description,
}: {
  number: string;
  title: string;
  description: string;
}) {
  return (
    <div className="mb-4">
      <h3 className="text-base font-semibold">
        {number}. {title}
      </h3>

      <p className="mt-1 text-sm text-muted-foreground">
        {description}
      </p>
    </div>
  );
}

function Field({
  label,
  help,
  children,
}: {
  label: string;
  help?: string;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-2">
      <label className="text-sm font-medium">
        {label}
      </label>

      {children}

      {help && (
        <p className="text-xs text-muted-foreground">
          {help}
        </p>
      )}
    </div>
  );
}

function MeasurementField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <Field label={label}>
      <div className="relative">
        <input
          type="number"
          min="0"
          step="0.01"
          value={value}
          onChange={(event) =>
            onChange(event.target.value)
          }
          className={`${inputClass} pr-10`}
        />

        <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">
          m
        </span>
      </div>
    </Field>
  );
}

function MassField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <Field label={label}>
      <div className="relative">
        <input
          type="number"
          min="0"
          step="0.01"
          value={value}
          onChange={(event) =>
            onChange(event.target.value)
          }
          className={`${inputClass} pr-10`}
        />

        <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">
          t
        </span>
      </div>
    </Field>
  );
}

function SanityRangeRow({
  label,
  minimum,
  maximum,
  onMinimumChange,
  onMaximumChange,
}: {
  label: string;
  minimum: string;
  maximum: string;
  onMinimumChange: (value: string) => void;
  onMaximumChange: (value: string) => void;
}) {
  return (
    <div className="grid grid-cols-3 items-center gap-3 border-t border-border px-4 py-3">
      <span className="text-sm font-medium">
        {label}
      </span>

      <div className="relative">
        <input
          type="number"
          min="0"
          step="0.01"
          value={minimum}
          onChange={(event) =>
            onMinimumChange(
              event.target.value
            )
          }
          className={`${inputClass} pr-8`}
        />

        <span className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">
          m
        </span>
      </div>

      <div className="relative">
        <input
          type="number"
          min="0"
          step="0.01"
          value={maximum}
          onChange={(event) =>
            onMaximumChange(
              event.target.value
            )
          }
          className={`${inputClass} pr-8`}
        />

        <span className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">
          m
        </span>
      </div>
    </div>
  );
}