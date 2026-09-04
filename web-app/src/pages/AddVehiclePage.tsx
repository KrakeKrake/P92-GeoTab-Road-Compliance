import { useState } from 'react';
import { useNavigate } from '@tanstack/react-router';

type AxleConfigurationForm = {
  clientId: string;
  axleConfigId: string;
  displayName: string;
  maxLength: string;
  accessPath: string;
  axleGroupMassesCsv: string;
  gmlMass: string;
  cmlMass: string;
  hmlMass: string;
  note: string;
};

const CATEGORY_OPTIONS = [
  {
    id: 'rigid_trucks',
    name: 'Rigid Trucks',
  },
  {
    id: 'articulated_vehicles',
    name: 'Prime Mover + Semitrailer',
  },
  {
    id: 'multi_combination',
    name: 'Multi-Combination Vehicles',
  },
];

function createEmptyAxleConfiguration(): AxleConfigurationForm {
  return {
    clientId: `${Date.now()}-${Math.random()}`,
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

const AddVehiclePage = () => {
  const navigate = useNavigate();

  // =========================================================
  // Category
  // =========================================================
  const [categoryId, setCategoryId] = useState('');

  const selectedCategory = CATEGORY_OPTIONS.find(
    (category) => category.id === categoryId
  );

  const categoryName = selectedCategory?.name ?? '';

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

  const [allowCustomDimensions, setAllowCustomDimensions] =
    useState(true);

  const [requiredLicence, setRequiredLicence] =
    useState('');

  // =========================================================
  // Default Dimensions
  // =========================================================
  const [defaultWidth, setDefaultWidth] = useState('');
  const [defaultHeight, setDefaultHeight] = useState('');
  const [defaultLength, setDefaultLength] = useState('');

  // =========================================================
  // Dimension Rule
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
  // Input Sanity Range
  // =========================================================
  const [minWidth, setMinWidth] = useState('');
  const [maxWidth, setMaxWidth] = useState('');

  const [minHeight, setMinHeight] = useState('');
  const [maxHeight, setMaxHeight] = useState('');

  const [minLength, setMinLength] = useState('');
  const [maxLength, setMaxLength] = useState('');

  // =========================================================
  // Axle Configurations
  // =========================================================
  const [axleConfigurations, setAxleConfigurations] =
    useState<AxleConfigurationForm[]>([
      createEmptyAxleConfiguration(),
    ]);

  // =========================================================
  // Submit state
  // =========================================================
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] =
    useState('');

  // =========================================================
  // Helpers
  // =========================================================
  function numberOrNull(value: string) {
    if (value.trim() === '') {
      return null;
    }

    return Number(value);
  }

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

  function removeAxleConfiguration(clientId: string) {
    setAxleConfigurations((current) =>
      current.filter(
        (configuration) =>
          configuration.clientId !== clientId
      )
    );
  }

  function parseAxleGroupMasses(csv: string) {
    if (!csv.trim()) {
      return [];
    }

    return csv
      .split(',')
      .map((value) => value.trim())
      .filter((value) => value !== '')
      .map((value) => Number(value));
  }

  // =========================================================
  // Frontend Validation
  // =========================================================
  function validateForm(): string | null {
    if (!categoryId) {
      return 'Please select a vehicle category.';
    }

    if (!templateId.trim()) {
      return 'Template ID is required.';
    }

    if (!templateName.trim()) {
      return 'Template name is required.';
    }

    if (!baseType) {
      return 'Please select a base type.';
    }

    if (!profileId.trim()) {
      return 'Profile ID is required.';
    }

    if (!displayName.trim()) {
      return 'Display name is required.';
    }

    if (!vehicleFamily) {
      return 'Please select a vehicle family.';
    }

    if (!combinationType) {
      return 'Please select a combination type.';
    }

    if (!requiredLicence) {
      return 'Please select a required licence class.';
    }

    if (
      defaultWidth === '' ||
      defaultHeight === '' ||
      defaultLength === ''
    ) {
      return 'All default dimensions are required.';
    }

    if (
      Number(defaultWidth) <= 0 ||
      Number(defaultHeight) <= 0 ||
      Number(defaultLength) <= 0
    ) {
      return 'Default dimensions must be greater than zero.';
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
      return 'All input sanity range values are required.';
    }

    const minimumWidth = Number(minWidth);
    const maximumWidth = Number(maxWidth);

    const minimumHeight = Number(minHeight);
    const maximumHeight = Number(maxHeight);

    const minimumLength = Number(minLength);
    const maximumLength = Number(maxLength);

    if (minimumWidth > maximumWidth) {
      return 'Minimum width cannot be greater than maximum width.';
    }

    if (minimumHeight > maximumHeight) {
      return 'Minimum height cannot be greater than maximum height.';
    }

    if (minimumLength > maximumLength) {
      return 'Minimum length cannot be greater than maximum length.';
    }

    if (
      Number(defaultWidth) < minimumWidth ||
      Number(defaultWidth) > maximumWidth
    ) {
      return 'Default width must be within the input sanity width range.';
    }

    if (
      Number(defaultHeight) < minimumHeight ||
      Number(defaultHeight) > maximumHeight
    ) {
      return 'Default height must be within the input sanity height range.';
    }

    if (
      Number(defaultLength) < minimumLength ||
      Number(defaultLength) > maximumLength
    ) {
      return 'Default length must be within the input sanity length range.';
    }

    if (Number(widthLimit) > maximumWidth) {
      return 'Legal width limit cannot exceed maximum sanity width.';
    }

    if (Number(heightLimit) > maximumHeight) {
      return 'Legal height limit cannot exceed maximum sanity height.';
    }

    if (Number(lengthLimit) > maximumLength) {
      return 'Legal length limit cannot exceed maximum sanity length.';
    }

    if (
      axleCount !== '' &&
      (!Number.isInteger(Number(axleCount)) ||
        Number(axleCount) <= 0)
    ) {
      return 'Axle count must be a positive whole number.';
    }

    if (
      axleConfigurable &&
      axleConfigurations.length === 0
    ) {
      return 'At least one axle configuration is required.';
    }

    const seenIds = new Set<string>();

    for (
      let index = 0;
      index < axleConfigurations.length;
      index++
    ) {
      const config = axleConfigurations[index];

      if (!config) {
        continue;
      }

      const position = index + 1;

      if (!config.axleConfigId.trim()) {
        return `Axle configuration ${position}: ID is required.`;
      }

      const normalisedId = config.axleConfigId
        .trim()
        .toUpperCase()
        .replaceAll(' ', '_')
        .replaceAll('-', '_');

      if (seenIds.has(normalisedId)) {
        return `Duplicate axle configuration ID: ${normalisedId}`;
      }

      seenIds.add(normalisedId);

      if (!config.displayName.trim()) {
        return `Axle configuration ${position}: display name is required.`;
      }

      if (config.maxLength === '') {
        return `Axle configuration ${position}: maximum length is required.`;
      }

      const axleMaxLength = Number(
        config.maxLength
      );

      if (
        !Number.isFinite(axleMaxLength) ||
        axleMaxLength <= 0
      ) {
        return `Axle configuration ${position}: maximum length must be greater than zero.`;
      }

      if (
        axleMaxLength < minimumLength ||
        axleMaxLength > maximumLength
      ) {
        return `Axle configuration ${position}: maximum length must be between ${minimumLength} m and ${maximumLength} m.`;
      }

      if (!config.accessPath) {
        return `Axle configuration ${position}: access path is required.`;
      }

      const groupMasses = parseAxleGroupMasses(
        config.axleGroupMassesCsv
      );

      if (
        groupMasses.some(
          (mass) =>
            !Number.isFinite(mass) ||
            mass < 0
        )
      ) {
        return `Axle configuration ${position}: axle group masses must be valid non-negative numbers separated by commas.`;
      }

      for (const [
        label,
        value,
      ] of [
        ['GML', config.gmlMass],
        ['CML', config.cmlMass],
        ['HML', config.hmlMass],
      ]) {
        if (
          value !== '' &&
          (!Number.isFinite(Number(value)) ||
            Number(value) < 0)
        ) {
          return `Axle configuration ${position}: ${label} mass must be zero or greater.`;
        }
      }
    }

    return null;
  }

  // =========================================================
  // Submit
  // =========================================================
  async function saveVehicle() {
    setError('');
    setSuccessMessage('');

    const validationError = validateForm();

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
          combination_type: combinationType,

          gvm_category:
            gvmCategory || null,

          axle_count:
            axleCount === ''
              ? null
              : Number(axleCount),

          axle_configurable: axleConfigurable,

          default_width_m: Number(defaultWidth),
          default_height_m: Number(defaultHeight),
          default_length_m: Number(defaultLength),

          allow_custom_dimensions:
            allowCustomDimensions,

          required_licence_class_id:
            requiredLicence,
        },

        dimension_rule: {
          rule_name: ruleName,
          width_limit_m: Number(widthLimit),
          height_limit_m: Number(heightLimit),
          length_limit_m: Number(lengthLimit),

          classification_if_exceeded_limit:
            classificationIfExceeded,

          note: ruleNote,
        },

        input_sanity_range: {
          min_width_m: Number(minWidth),
          max_width_m: Number(maxWidth),

          min_height_m: Number(minHeight),
          max_height_m: Number(maxHeight),

          min_length_m: Number(minLength),
          max_length_m: Number(maxLength),
        },

        axle_configurations: axleConfigurable
          ? axleConfigurations.map(
              (configuration) => ({
                axle_config_id:
                  configuration.axleConfigId,

                display_name:
                  configuration.displayName,

                max_length_m: Number(
                  configuration.maxLength
                ),

                access_path:
                  configuration.accessPath,

                axle_group_masses_t:
                  parseAxleGroupMasses(
                    configuration.axleGroupMassesCsv
                  ),

                gml_mass_t: numberOrNull(
                  configuration.gmlMass
                ),

                cml_mass_t: numberOrNull(
                  configuration.cmlMass
                ),

                hml_mass_t: numberOrNull(
                  configuration.hmlMass
                ),

                note: configuration.note,
              })
            )
          : [],
      };

      console.log(
        'Add vehicle payload:',
        payload
      );

      const response = await fetch(
        '/api/compliance/admin/vehicles',
        {
          method: 'POST',
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
            'Failed to add vehicle.'
        );
      }

      setSuccessMessage(
        `Vehicle added successfully. Profile: ${data.profile_id}`
      );

      window.scrollTo({
        top: 0,
        behavior: 'smooth',
      });
    } catch (error) {
      console.error(
        'Failed to add vehicle:',
        error
      );

      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError(
          'Failed to add vehicle.'
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

        {/* =====================================================
            PAGE HEADER
        ====================================================== */}
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
            className="rounded-md border border-border px-4 py-2 text-sm font-medium transition-colors hover:bg-accent"
          >
            Back to Map
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 rounded-md border border-destructive/30 bg-destructive/10 p-4">
            <p className="text-sm font-semibold text-destructive">
              Unable to add vehicle
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
              Vehicle Added
            </p>

            <p className="mt-1 text-sm text-muted-foreground">
              {successMessage}
            </p>
          </div>
        )}

        <section className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <div className="mb-8">
            <h1 className="text-2xl font-semibold">
              Add Vehicle Type
            </h1>

            <p className="mt-2 text-sm text-muted-foreground">
              Add a new heavy vehicle profile and its
              compliance configuration.
            </p>
          </div>

          <div className="flex flex-col gap-8">

            {/* =====================================================
                1 — CATEGORY
            ====================================================== */}
            <section>
              <SectionTitle
                number="1"
                title="Vehicle Category"
                description="Select the broad category for this vehicle."
              />

              <div className="grid gap-4 md:grid-cols-2">
                <Field label="Category">
                  <select
                    value={categoryId}
                    onChange={(event) =>
                      setCategoryId(
                        event.target.value
                      )
                    }
                    className={inputClass}
                  >
                    <option value="">
                      — Select category —
                    </option>

                    {CATEGORY_OPTIONS.map(
                      (category) => (
                        <option
                          key={category.id}
                          value={category.id}
                        >
                          {category.name}
                        </option>
                      )
                    )}
                  </select>
                </Field>

                <Field label="Category Name">
                  <input
                    value={categoryName}
                    readOnly
                    className={`${inputClass} bg-muted text-muted-foreground`}
                  />
                </Field>
              </div>
            </section>

            <Divider />

            {/* =====================================================
                2 — TEMPLATE
            ====================================================== */}
            <section>
              <SectionTitle
                number="2"
                title="Vehicle Template"
                description="Define the reusable vehicle type."
              />

              <div className="grid gap-4 md:grid-cols-2">
                <Field
                  label="Template ID"
                  help="Must be a new unique template ID."
                >
                  <input
                    value={templateId}
                    onChange={(event) =>
                      setTemplateId(
                        event.target.value.toUpperCase()
                      )
                    }
                    placeholder="e.g. A_DOUBLE"
                    className={inputClass}
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
                    placeholder="e.g. A-double"
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
                    <option value="">
                      — Select base type —
                    </option>

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

            {/* =====================================================
                3 — PROFILE
            ====================================================== */}
            <section>
              <SectionTitle
                number="3"
                title="Vehicle Profile"
                description="Configure how this vehicle appears in the compliance engine."
              />

              <div className="grid gap-4 md:grid-cols-2">
                <Field label="Profile ID">
                  <input
                    value={profileId}
                    onChange={(event) =>
                      setProfileId(
                        event.target.value.toUpperCase()
                      )
                    }
                    placeholder="e.g. STANDARD_A_DOUBLE"
                    className={inputClass}
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
                    placeholder="e.g. A-Double Combination"
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
                    <option value="">
                      — Select vehicle family —
                    </option>

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
                    <option value="">
                      — Select combination type —
                    </option>

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
                    <option value="">
                      — Select licence —
                    </option>

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
                  help="Leave blank when axle configuration varies."
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
                    placeholder="Optional"
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

            {/* =====================================================
                4 — DEFAULT DIMENSIONS
            ====================================================== */}
            <section>
              <SectionTitle
                number="4"
                title="Default Dimensions"
                description="Default dimensions shown when this vehicle is selected."
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

            {/* =====================================================
                5 — DIMENSION RULE
            ====================================================== */}
            <section>
              <SectionTitle
                number="5"
                title="Dimension Rule"
                description="Define the legal dimension limits used by the classification engine."
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
                      placeholder="e.g. A-Double dimension rule"
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
                      placeholder="Optional regulatory note"
                      className="w-full resize-y rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
                    />
                  </Field>
                </div>
              </div>
            </section>

            <Divider />

            {/* =====================================================
                6 — SANITY RANGE
            ====================================================== */}
            <section>
              <SectionTitle
                number="6"
                title="Input Sanity Range"
                description="Define acceptable ranges for custom vehicle dimensions."
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
                  onMinimumChange={setMinWidth}
                  onMaximumChange={setMaxWidth}
                />

                <SanityRangeRow
                  label="Height"
                  minimum={minHeight}
                  maximum={maxHeight}
                  onMinimumChange={setMinHeight}
                  onMaximumChange={setMaxHeight}
                />

                <SanityRangeRow
                  label="Length"
                  minimum={minLength}
                  maximum={maxLength}
                  onMinimumChange={setMinLength}
                  onMaximumChange={setMaxLength}
                />
              </div>
            </section>

            <Divider />

            {/* =====================================================
                7 — AXLE CONFIGURATIONS
            ====================================================== */}
            <section>
              <div className="mb-5 flex items-start justify-between gap-4">
                <div>
                  <h3 className="text-base font-semibold">
                    7. Axle Configurations
                  </h3>

                  <p className="mt-1 text-sm text-muted-foreground">
                    Configure axle layouts, access
                    classification and mass limits.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={addAxleConfiguration}
                  className="shrink-0 rounded-md border border-border bg-background px-3 py-2 text-sm font-medium transition-colors hover:bg-accent"
                >
                  + Add Configuration
                </button>
              </div>

              {!axleConfigurable && (
                <div className="mb-4 rounded-md bg-muted p-4 text-sm text-muted-foreground">
                  Axle configuration selection is disabled
                  for this vehicle. No axle configurations
                  will be submitted.
                </div>
              )}

              {axleConfigurable && (
                <div className="flex flex-col gap-5">
                  {axleConfigurations.map(
                    (configuration, index) => (
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

                          <button
                            type="button"
                            onClick={() =>
                              removeAxleConfiguration(
                                configuration.clientId
                              )
                            }
                            className="text-sm font-medium text-destructive hover:underline"
                          >
                            Remove
                          </button>
                        </div>

                        <div className="grid gap-4 md:grid-cols-2">
                          <Field label="Axle Configuration ID">
                            <input
                              value={
                                configuration.axleConfigId
                              }
                              onChange={(event) =>
                                updateAxleConfiguration(
                                  configuration.clientId,
                                  'axleConfigId',
                                  event.target.value.toUpperCase()
                                )
                              }
                              placeholder="e.g. A_DOUBLE_8_AXLE"
                              className={
                                inputClass
                              }
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
                              placeholder="e.g. 8 Axle A-double"
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
                            onChange={(value) =>
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
                              help="Enter masses in order, separated by commas. Example: 6, 16.5, 20"
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
                                placeholder="6, 16.5, 20"
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
                              onChange={(value) =>
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
                              onChange={(value) =>
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
                              onChange={(value) =>
                                updateAxleConfiguration(
                                  configuration.clientId,
                                  'hmlMass',
                                  value
                                )
                              }
                            />
                          </div>

                          <p className="mt-2 text-xs text-muted-foreground">
                            Leave a mass scheme blank if
                            it does not apply to this axle
                            configuration.
                          </p>
                        </div>

                        <div className="mt-5">
                          <Field label="Configuration Note">
                            <textarea
                              rows={2}
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
                              placeholder="Optional note"
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

            {/* =====================================================
                ACTIONS
            ====================================================== */}
            <div className="flex flex-col gap-3 sm:flex-row sm:justify-end">
              <button
                type="button"
                onClick={() =>
                  navigate({ to: '/' })
                }
                disabled={saving}
                className="h-10 rounded-md border border-border bg-background px-5 text-sm font-medium transition-colors hover:bg-accent disabled:opacity-50"
              >
                Cancel
              </button>

              <button
                type="button"
                onClick={saveVehicle}
                disabled={saving}
                className="h-10 rounded-md bg-primary px-6 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {saving
                  ? 'Adding Vehicle...'
                  : 'Add Vehicle Type'}
              </button>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
};

export default AddVehiclePage;

// =========================================================
// Shared styles / components
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
  children: React.ReactNode;
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
            onMinimumChange(event.target.value)
          }
          placeholder="Min"
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
            onMaximumChange(event.target.value)
          }
          placeholder="Max"
          className={`${inputClass} pr-8`}
        />

        <span className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">
          m
        </span>
      </div>
    </div>
  );
}