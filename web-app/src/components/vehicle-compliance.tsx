import { useEffect, useRef, useState } from 'react';
import { useComplianceStore } from '@/stores/compliance-store';
interface User {
  user_id: number;
  email: string;
  username: string;
  licence_class_id?: string | null;
  favourite_profile_id?: string | null;
}

interface ProfileOption {
  profile_id: string;
  display_name: string;
}

interface MassLimit {
  mass_scheme_id: string;
  mass_limit_t: number | null;
  applicable: boolean;
}

interface AxleConfiguration {
  config_id: string;
  display_name: string;
  max_length_m: number;
  access_path?: string | null;
  note?: string | null;
  mass_limits: MassLimit[];
}

interface VehicleProfile {
  profile_id: string;
  display_name: string;
  template_id: string;
  vehicle_family?: string | null;
  combination_type?: string | null;
  gvm_category?: string | null;
  axle_count?: number | null;
  axle_configurable?: boolean;
  default_width_m: number;
  default_height_m: number;
  default_length_m: number;
  allow_custom_dimensions?: boolean;
}

interface TemplateQuestion {
  name: string;
  type: string;
  label: string;
}

interface VehicleTemplate {
  vehicle_id: string;
  display_name: string;
  base_type?: string | null;
  extra_questions: TemplateQuestion[];
}

interface DimensionRanges {
  template_id: string;
  min_width_m: number;
  max_width_m: number;
  min_height_m: number;
  max_height_m: number;
  min_length_m: number;
  max_length_m: number;
}

interface VehicleFormData {
  profile: VehicleProfile;
  template: VehicleTemplate;
  dimension_ranges: DimensionRanges | null;
  axle_configurations: AxleConfiguration[];
}

interface ClassificationResult {
  profile_id: string;
  display_name: string;
  template_id: string;
  status: string;
  classification: string;
  reason: string;
  used_dimensions: Record<string, number>;
  missing_fields: string[];
  warnings: string[];
}

interface MassValidationResult {
  status: string;
  compliant: boolean;
  reason: string;
  selected_limit_t: number | null;
}

interface ComplianceResult {
  classification_result: ClassificationResult;
  mass_validation_result: MassValidationResult;
}

type ExtraAnswerValue = boolean | string;

type Answers = Record<string, boolean | number>;

export const VehicleCompliance = () => {

  const setAppliedVehicle = useComplianceStore(
    (state) => state.setAppliedVehicle
  );

  const clearAppliedVehicle = useComplianceStore(
    (state) => state.clearAppliedVehicle
  );
  const [user, setUser] = useState<User | null>(null);

  const [licenceClass, setLicenceClass] = useState('');

  const [profiles, setProfiles] = useState<ProfileOption[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState('');

  const [vehicleFormData, setVehicleFormData] =
    useState<VehicleFormData | null>(null);

  const [selectedAxleConfigId, setSelectedAxleConfigId] =
    useState('');

  const [selectedMassScheme, setSelectedMassScheme] =
    useState('');

  const [operatingMass, setOperatingMass] = useState('');

  const [useCustomDimensions, setUseCustomDimensions] =
    useState(false);

  const [customWidth, setCustomWidth] = useState('');
  const [customHeight, setCustomHeight] = useState('');
  const [customLength, setCustomLength] = useState('');

  const [extraAnswers, setExtraAnswers] =
    useState<Record<string, ExtraAnswerValue>>({});

  const [profilesLoading, setProfilesLoading] = useState(false);
  const [formLoading, setFormLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [error, setError] = useState('');
  const [result, setResult] =
    useState<ComplianceResult | null>(null);

  const initialFavouriteLoaded = useRef(false);

  /*
   * Load logged-in user or guest licence.
   */
  function loadUser() {
    const storedUser = localStorage.getItem('user');

    if (!storedUser) {
      setUser(null);

      const guestLicence = sessionStorage.getItem(
        'guest_selected_licence_class'
      );

      setLicenceClass(guestLicence ?? '');

      initialFavouriteLoaded.current = true;

      return;
    }

    try {
      const parsedUser = JSON.parse(storedUser) as User;

      setUser(parsedUser);

      if (parsedUser.licence_class_id) {
        setLicenceClass(parsedUser.licence_class_id);
      } else {
        setLicenceClass('');
      }

      initialFavouriteLoaded.current = false;
    } catch (error) {
      console.error('Unable to read saved user:', error);

      setUser(null);
      setLicenceClass('');
    }
  }

  /*
   * Listen for login/logout.
   */
  useEffect(() => {
    loadUser();

    window.addEventListener('auth-updated', loadUser);

    return () => {
      window.removeEventListener('auth-updated', loadUser);
    };
  }, []);

  /*
   * Load profiles allowed by licence.
   */
  useEffect(() => {
    async function loadProfiles() {
      setProfiles([]);
      setSelectedProfileId('');

      setVehicleFormData(null);
      setSelectedAxleConfigId('');
      setSelectedMassScheme('');
      setOperatingMass('');

      setUseCustomDimensions(false);
      setCustomWidth('');
      setCustomHeight('');
      setCustomLength('');

      setExtraAnswers({});
      setResult(null);
      setError('');

      if (!licenceClass) {
        return;
      }

      setProfilesLoading(true);

      try {
        const response = await fetch(
          `/api/compliance/profiles-by-licence/${licenceClass}`
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(
            data.detail || 'Failed to load vehicle profiles.'
          );
        }

        const loadedProfiles: ProfileOption[] = Array.isArray(data)
          ? data
          : [];

        setProfiles(loadedProfiles);

        /*
         * Automatically select the user's favourite vehicle
         * on initial load.
         */
        if (
          user?.favourite_profile_id &&
          !initialFavouriteLoaded.current
        ) {
          const favouriteExists = loadedProfiles.some(
            (profile) =>
              profile.profile_id === user.favourite_profile_id
          );

          if (favouriteExists) {
            setSelectedProfileId(
              user.favourite_profile_id
            );
          }

          initialFavouriteLoaded.current = true;
        }
      } catch (error) {
        console.error(
          'Failed to load vehicle profiles:',
          error
        );

        if (error instanceof Error) {
          setError(error.message);
        } else {
          setError('Failed to load vehicle profiles.');
        }
      } finally {
        setProfilesLoading(false);
      }
    }

    loadProfiles();
  }, [licenceClass, user]);

  /*
   * Load full vehicle form data.
   */
  useEffect(() => {
    async function loadVehicleFormData() {
      setVehicleFormData(null);

      setSelectedAxleConfigId('');
      setSelectedMassScheme('');
      setOperatingMass('');

      setUseCustomDimensions(false);
      setCustomWidth('');
      setCustomHeight('');
      setCustomLength('');

      setExtraAnswers({});
      setResult(null);
      setError('');

      if (!selectedProfileId) {
        return;
      }

      setFormLoading(true);

      try {
        const response = await fetch(
          `/api/compliance/vehicle-form-data/${selectedProfileId}`
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(
            data.detail ||
            'Failed to load vehicle information.'
          );
        }

        const loadedData = data as VehicleFormData;

        setVehicleFormData(loadedData);

        /*
         * Initialise additional question answers.
         */
        const initialAnswers: Record<
          string,
          ExtraAnswerValue
        > = {};

        loadedData.template.extra_questions.forEach(
          (question) => {
            initialAnswers[question.name] = '';
          }
        );

        setExtraAnswers(initialAnswers);
      } catch (error) {
        console.error(
          'Failed to load vehicle form data:',
          error
        );

        if (error instanceof Error) {
          setError(error.message);
        } else {
          setError(
            'Failed to load vehicle information.'
          );
        }
      } finally {
        setFormLoading(false);
      }
    }

    loadVehicleFormData();
  }, [selectedProfileId]);

  /*
   * Licence changed.
   */
  function handleLicenceChange(
    event: React.ChangeEvent<HTMLSelectElement>
  ) {
    const newLicence = event.target.value;

    setLicenceClass(newLicence);

    if (!user) {
      if (newLicence) {
        sessionStorage.setItem(
          'guest_selected_licence_class',
          newLicence
        );
      } else {
        sessionStorage.removeItem(
          'guest_selected_licence_class'
        );
      }
    }
  }

  /*
   * Profile changed.
   */
  function handleProfileChange(
    event: React.ChangeEvent<HTMLSelectElement>
  ) {
    setSelectedProfileId(event.target.value);
  }

  /*
   * Axle changed.
   */
  function handleAxleChange(
    event: React.ChangeEvent<HTMLSelectElement>
  ) {
    setSelectedAxleConfigId(event.target.value);

    setSelectedMassScheme('');
    setResult(null);
    setError('');
  }

  /*
   * Additional question changed.
   */
  function handleExtraAnswer(
    question: TemplateQuestion,
    value: string
  ) {
    if (question.type === 'bool') {
      if (value === '') {
        setExtraAnswers((current) => ({
          ...current,
          [question.name]: '',
        }));

        return;
      }

      setExtraAnswers((current) => ({
        ...current,
        [question.name]: value === 'true',
      }));

      return;
    }

    setExtraAnswers((current) => ({
      ...current,
      [question.name]: value,
    }));
  }

  /*
   * Current axle.
   */
  const currentAxleConfig =
    vehicleFormData?.axle_configurations.find(
      (config) =>
        config.config_id === selectedAxleConfigId
    ) ?? null;

  /*
   * Applicable mass schemes.
   */
  const applicableMassLimits =
    currentAxleConfig?.mass_limits.filter(
      (limit) =>
        limit.applicable &&
        limit.mass_limit_t !== null
    ) ?? [];

  const dimensionRanges =
    vehicleFormData?.dimension_ranges ?? null;

  const templateQuestions =
    vehicleFormData?.template.extra_questions ?? [];

  /*
   * Build answers object expected by Flask.
   */
  function buildAnswers(): Answers {
    const answers: Answers = {};

    if (useCustomDimensions) {
      answers.overall_width_m = Number(customWidth);
      answers.overall_height_m = Number(customHeight);
      answers.overall_length_m = Number(customLength);
    }

    templateQuestions.forEach((question) => {
      const value = extraAnswers[question.name];

      if (
        value === undefined ||
        value === ''
      ) {
        return;
      }

      if (question.type === 'bool') {
        answers[question.name] = value === true;
      } else {
        answers[question.name] = Number(value);
      }
    });

    return answers;
  }

  /*
   * Check all frontend inputs before sending
   * the request to Flask.
   */
  function validateForm(): string | null {
    if (!licenceClass) {
      return 'Please select a licence class first.';
    }

    if (!selectedProfileId || !vehicleFormData) {
      return 'Please select a vehicle profile first.';
    }

    if (!selectedAxleConfigId || !currentAxleConfig) {
      return 'Please select an axle configuration first.';
    }

    if (!selectedMassScheme) {
      return 'Please select a mass scheme.';
    }

    const mass = Number(operatingMass);

    if (
      operatingMass === '' ||
      !Number.isFinite(mass) ||
      mass <= 0
    ) {
      return 'Please enter a valid operating mass in tonnes.';
    }

    if (useCustomDimensions) {
      if (customWidth === '') {
        return 'Please enter the overall width.';
      }

      if (customHeight === '') {
        return 'Please enter the overall height.';
      }

      if (customLength === '') {
        return 'Please enter the overall length.';
      }

      const width = Number(customWidth);
      const height = Number(customHeight);
      const length = Number(customLength);

      if (
        !Number.isFinite(width) ||
        !Number.isFinite(height) ||
        !Number.isFinite(length)
      ) {
        return 'Please enter valid vehicle dimensions.';
      }

      if (dimensionRanges) {
        if (
          width < dimensionRanges.min_width_m ||
          width > dimensionRanges.max_width_m
        ) {
          return `Width must be between ${dimensionRanges.min_width_m} m and ${dimensionRanges.max_width_m} m.`;
        }

        if (
          height < dimensionRanges.min_height_m ||
          height > dimensionRanges.max_height_m
        ) {
          return `Height must be between ${dimensionRanges.min_height_m} m and ${dimensionRanges.max_height_m} m.`;
        }

        if (
          length < dimensionRanges.min_length_m ||
          length > dimensionRanges.max_length_m
        ) {
          return `Length must be between ${dimensionRanges.min_length_m} m and ${dimensionRanges.max_length_m} m.`;
        }
      }
    }

    /*
     * The current classifier expects the template
     * questions to have an answer.
     */
    for (const question of templateQuestions) {
      const answer = extraAnswers[question.name];

      if (
        answer === undefined ||
        answer === ''
      ) {
        return `Please answer: ${question.label}`;
      }

      if (
        question.type !== 'bool' &&
        !Number.isFinite(Number(answer))
      ) {
        return `Please enter a valid value for: ${question.label}`;
      }
    }

    return null;
  }

  /*
   * Send complete compliance request to Flask.
   */
  async function classifyAndValidate() {
    setError('');
    setResult(null);

    const validationError = validateForm();

    if (validationError) {
      setError(validationError);
      return;
    }

    setSubmitting(true);

    try {
      const payload = {
        profile_id: selectedProfileId,
        axle_config_id: selectedAxleConfigId,
        mass_scheme: selectedMassScheme,
        operating_mass_t: Number(operatingMass),
        custom_dimensions: useCustomDimensions,
        answers: buildAnswers(),
      };

      console.log(
        'Classify and validate payload:',
        payload
      );

      const response = await fetch(
        '/api/compliance/classify-and-validate',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
          'Failed to classify and validate vehicle.'
        );
      }

      const complianceResult =
        data as ComplianceResult;

      setResult(complianceResult);

      console.log(
        'Compliance result:',
        complianceResult
      );

      /*
       * Only apply a vehicle to routing when:
       *
       * 1. the mass is compliant
       * 2. the classifier returned a recognised vehicle class
       *
       * Class 1, Class 2 and Class 3 are all valid classifications
       * for routing purposes.
       */
      const vehicleClass =
        complianceResult.classification_result
          .classification;

      const classificationValid =
        vehicleClass !== 'invalid_input' &&
        vehicleClass !== 'unknown';

      if (
        complianceResult.mass_validation_result
          .compliant &&
        classificationValid &&
        vehicleFormData &&
        currentAxleConfig
      ) {
        const widthM = useCustomDimensions
          ? Number(customWidth)
          : vehicleFormData.profile.default_width_m;

        const heightM = useCustomDimensions
          ? Number(customHeight)
          : vehicleFormData.profile.default_height_m;

        /*
         * The selected axle configuration may provide
         * the applicable maximum/default routing length.
         *
         * For custom dimensions, use exactly what the user entered.
         */
        const lengthM = useCustomDimensions
          ? Number(customLength)
          : vehicleFormData.profile.default_length_m;

        setAppliedVehicle({
          profileId:
            vehicleFormData.profile.profile_id,

          profileName:
            vehicleFormData.profile.display_name,

          templateId:
            vehicleFormData.profile.template_id,

          vehicleType:
            vehicleFormData.template.display_name,

          vehicleClass,

          axleConfigId:
            currentAxleConfig.config_id,

          axleConfigName:
            currentAxleConfig.display_name,

          massScheme:
            selectedMassScheme,

          accessPath:
            currentAxleConfig.access_path ??
            'general_access',

          widthM,
          heightM,
          lengthM,

          operatingMassT:
            Number(operatingMass),
        });

        console.log(
          'Vehicle applied to routing store.'
        );
      } else {
        /*
         * Do not leave an old valid vehicle applied when
         * the newest compliance check fails.
         */
        clearAppliedVehicle();

        console.log(
          'Vehicle was not applied because it did not pass validation.'
        );
      }


    } catch (error) {
      console.error(
        'Classification failed:',
        error
      );

      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError(
          'Failed to classify and validate vehicle.'
        );
      }
    } finally {
      setSubmitting(false);
    }
  }

  /*
   * Clear vehicle inputs while retaining
   * licence/profile selection.
   */
  function resetForm() {
    setSelectedAxleConfigId('');
    setSelectedMassScheme('');
    setOperatingMass('');

    setUseCustomDimensions(false);
    setCustomWidth('');
    setCustomHeight('');
    setCustomLength('');

    const resetAnswers: Record<
      string,
      ExtraAnswerValue
    > = {};

    templateQuestions.forEach((question) => {
      resetAnswers[question.name] = '';
    });

    setExtraAnswers(resetAnswers);

    setResult(null);
    setError('');
  }

  function formatClassification(
    classification: string
  ) {
    if (classification === 'general_access') {
      return 'General Access';
    }

    if (classification === 'class_1') {
      return 'Class 1';
    }

    if (classification === 'class_2') {
      return 'Class 2';
    }

    if (classification === 'class_3') {
      return 'Class 3';
    }

    if (classification === 'invalid_input') {
      return 'Invalid Input';
    }

    if (classification === 'unknown') {
      return 'Unknown';
    }

    return classification;
  }

  function classificationIsPass(
    classification: string
  ) {
    return (
      classification !== 'class_3' &&
      classification !== 'invalid_input' &&
      classification !== 'unknown'
    );
  }

  return (
    <div className="p-4">
      {/* Header */}
      <div className="mb-5">
        <h3 className="text-base font-semibold text-foreground">
          Vehicle Compliance
        </h3>

        <p className="mt-1 text-sm text-muted-foreground">
          Configure your heavy vehicle before checking
          compliance.
        </p>
      </div>

      <div className="flex flex-col gap-5">
        {/* Licence */}
        <div className="flex flex-col gap-2">
          <label
            htmlFor="licence-class"
            className="text-sm font-medium text-foreground"
          >
            Licence Class
          </label>

          <select
            id="licence-class"
            value={licenceClass}
            onChange={handleLicenceChange}
            className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm text-foreground outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="">
              — Select licence class —
            </option>

            <option value="MC">
              MC — Multi Combination
            </option>

            <option value="HC">
              HC — Heavy Combination
            </option>

            <option value="HR">
              HR — Heavy Rigid
            </option>

            <option value="MR">
              MR — Medium Rigid
            </option>

            <option value="LR">
              LR — Light Rigid
            </option>
          </select>

          {user?.licence_class_id &&
            licenceClass ===
            user.licence_class_id && (
              <p className="text-xs text-muted-foreground">
                Using your saved licence class
              </p>
            )}
        </div>

        {/* Profile */}
        {licenceClass && (
          <div className="flex flex-col gap-2">
            <label
              htmlFor="vehicle-profile"
              className="text-sm font-medium text-foreground"
            >
              Vehicle Profile
            </label>

            <select
              id="vehicle-profile"
              value={selectedProfileId}
              onChange={handleProfileChange}
              disabled={profilesLoading}
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm text-foreground outline-none disabled:cursor-not-allowed disabled:opacity-50 focus:ring-2 focus:ring-ring"
            >
              <option value="">
                {profilesLoading
                  ? 'Loading vehicle profiles...'
                  : '— Select vehicle profile —'}
              </option>

              {profiles.map((profile) => (
                <option
                  key={profile.profile_id}
                  value={profile.profile_id}
                >
                  {profile.display_name}
                </option>
              ))}
            </select>

            {user?.favourite_profile_id &&
              selectedProfileId ===
              user.favourite_profile_id && (
                <p className="text-xs text-muted-foreground">
                  Using your favourite vehicle profile
                </p>
              )}
          </div>
        )}

        {/* Loading */}
        {formLoading && (
          <div className="rounded-md bg-muted p-3 text-sm text-muted-foreground">
            Loading vehicle information...
          </div>
        )}

        {/* Axle */}
        {vehicleFormData && (
          <div className="flex flex-col gap-2">
            <label
              htmlFor="axle-configuration"
              className="text-sm font-medium text-foreground"
            >
              Axle Configuration
            </label>

            <select
              id="axle-configuration"
              value={selectedAxleConfigId}
              onChange={handleAxleChange}
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm text-foreground outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">
                — Select axle configuration —
              </option>

              {vehicleFormData.axle_configurations.map(
                (config) => (
                  <option
                    key={config.config_id}
                    value={config.config_id}
                  >
                    {config.display_name}
                  </option>
                )
              )}
            </select>

            {vehicleFormData.axle_configurations
              .length === 0 && (
                <p className="text-xs text-muted-foreground">
                  No axle configurations are available.
                </p>
              )}
          </div>
        )}

        {/* Mass limits */}
        {currentAxleConfig && (
          <div>
            <h4 className="mb-2 text-sm font-medium text-foreground">
              Available Mass Limits
            </h4>

            <div className="overflow-hidden rounded-md border border-border">
              <table className="w-full text-sm">
                <thead className="bg-muted">
                  <tr>
                    <th className="px-3 py-2 text-left font-medium">
                      Scheme
                    </th>

                    <th className="px-3 py-2 text-left font-medium">
                      Maximum
                    </th>

                    <th className="px-3 py-2 text-left font-medium">
                      Status
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {currentAxleConfig.mass_limits.map(
                    (limit) => (
                      <tr
                        key={limit.mass_scheme_id}
                        className="border-t border-border"
                      >
                        <td className="px-3 py-2">
                          {limit.mass_scheme_id}
                        </td>

                        <td className="px-3 py-2 text-muted-foreground">
                          {limit.mass_limit_t !== null
                            ? `${limit.mass_limit_t} t`
                            : '—'}
                        </td>

                        <td className="px-3 py-2 text-muted-foreground">
                          {limit.applicable
                            ? 'Applicable'
                            : 'Not applicable'}
                        </td>
                      </tr>
                    )
                  )}
                </tbody>
              </table>
            </div>

            {currentAxleConfig.note && (
              <p className="mt-2 text-xs text-muted-foreground">
                Note: {currentAxleConfig.note}
              </p>
            )}
          </div>
        )}

        {/* Mass scheme */}
        {currentAxleConfig && (
          <div className="flex flex-col gap-2">
            <label
              htmlFor="mass-scheme"
              className="text-sm font-medium text-foreground"
            >
              Preferred Mass Scheme
            </label>

            <select
              id="mass-scheme"
              value={selectedMassScheme}
              onChange={(event) => {
                setSelectedMassScheme(
                  event.target.value
                );
                setResult(null);
                setError('');
              }}
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">
                — Select mass scheme —
              </option>

              {applicableMassLimits.map((limit) => (
                <option
                  key={limit.mass_scheme_id}
                  value={limit.mass_scheme_id}
                >
                  {limit.mass_scheme_id} — max{' '}
                  {limit.mass_limit_t} t
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Operating mass */}
        {currentAxleConfig && (
          <div className="flex flex-col gap-2">
            <label
              htmlFor="operating-mass"
              className="text-sm font-medium text-foreground"
            >
              Operating Mass
            </label>

            <div className="relative">
              <input
                id="operating-mass"
                type="number"
                min="0"
                step="0.1"
                value={operatingMass}
                onChange={(event) => {
                  setOperatingMass(
                    event.target.value
                  );
                  setResult(null);
                }}
                placeholder="e.g. 67"
                className="h-10 w-full rounded-md border border-input bg-background px-3 pr-20 text-sm outline-none placeholder:text-muted-foreground focus:ring-2 focus:ring-ring"
              />

              <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">
                tonnes
              </span>
            </div>
          </div>
        )}

        {/* Default dimensions */}
        {vehicleFormData && (
          <div>
            <h4 className="mb-2 text-sm font-medium">
              Default Vehicle Dimensions
            </h4>

            <div className="overflow-hidden rounded-md border border-border">
              <div className="flex justify-between border-b border-border px-3 py-2 text-sm">
                <span className="text-muted-foreground">
                  Width
                </span>

                <span className="font-medium">
                  {
                    vehicleFormData.profile
                      .default_width_m
                  }{' '}
                  m
                </span>
              </div>

              <div className="flex justify-between border-b border-border px-3 py-2 text-sm">
                <span className="text-muted-foreground">
                  Height
                </span>

                <span className="font-medium">
                  {
                    vehicleFormData.profile
                      .default_height_m
                  }{' '}
                  m
                </span>
              </div>

              <div className="flex justify-between px-3 py-2 text-sm">
                <span className="text-muted-foreground">
                  Length
                </span>

                <span className="font-medium">
                  {
                    vehicleFormData.profile
                      .default_length_m
                  }{' '}
                  m
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Custom dimensions */}
        {vehicleFormData && (
          <div className="flex flex-col gap-2">
            <label
              htmlFor="custom-dimensions"
              className="text-sm font-medium"
            >
              Custom Dimensions
            </label>

            <select
              id="custom-dimensions"
              value={
                useCustomDimensions ? 'yes' : 'no'
              }
              onChange={(event) => {
                setUseCustomDimensions(
                  event.target.value === 'yes'
                );

                setResult(null);
                setError('');
              }}
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="no">
                No — use default dimensions
              </option>

              <option value="yes">
                Yes — enter custom dimensions
              </option>
            </select>
          </div>
        )}

        {/* Custom dimension fields */}
        {vehicleFormData &&
          useCustomDimensions && (
            <div className="flex flex-col gap-4">
              {dimensionRanges && (
                <div className="rounded-md bg-muted p-3">
                  <p className="mb-2 text-xs font-medium">
                    Allowed Dimension Ranges
                  </p>

                  <div className="flex flex-col gap-1 text-xs text-muted-foreground">
                    <div className="flex justify-between">
                      <span>Width</span>
                      <span>
                        {
                          dimensionRanges.min_width_m
                        }
                        –
                        {
                          dimensionRanges.max_width_m
                        }{' '}
                        m
                      </span>
                    </div>

                    <div className="flex justify-between">
                      <span>Height</span>
                      <span>
                        {
                          dimensionRanges.min_height_m
                        }
                        –
                        {
                          dimensionRanges.max_height_m
                        }{' '}
                        m
                      </span>
                    </div>

                    <div className="flex justify-between">
                      <span>Length</span>
                      <span>
                        {
                          dimensionRanges.min_length_m
                        }
                        –
                        {
                          dimensionRanges.max_length_m
                        }{' '}
                        m
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Width */}
              <div className="flex flex-col gap-2">
                <label
                  htmlFor="custom-width"
                  className="text-sm font-medium"
                >
                  Overall Width
                </label>

                <div className="relative">
                  <input
                    id="custom-width"
                    type="number"
                    step="0.1"
                    min={
                      dimensionRanges?.min_width_m
                    }
                    max={
                      dimensionRanges?.max_width_m
                    }
                    value={customWidth}
                    onChange={(event) => {
                      setCustomWidth(
                        event.target.value
                      );
                      setResult(null);
                    }}
                    placeholder="Width"
                    className="h-10 w-full rounded-md border border-input bg-background px-3 pr-10 text-sm outline-none focus:ring-2 focus:ring-ring"
                  />

                  <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">
                    m
                  </span>
                </div>
              </div>

              {/* Height */}
              <div className="flex flex-col gap-2">
                <label
                  htmlFor="custom-height"
                  className="text-sm font-medium"
                >
                  Overall Height
                </label>

                <div className="relative">
                  <input
                    id="custom-height"
                    type="number"
                    step="0.1"
                    min={
                      dimensionRanges?.min_height_m
                    }
                    max={
                      dimensionRanges?.max_height_m
                    }
                    value={customHeight}
                    onChange={(event) => {
                      setCustomHeight(
                        event.target.value
                      );
                      setResult(null);
                    }}
                    placeholder="Height"
                    className="h-10 w-full rounded-md border border-input bg-background px-3 pr-10 text-sm outline-none focus:ring-2 focus:ring-ring"
                  />

                  <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">
                    m
                  </span>
                </div>
              </div>

              {/* Length */}
              <div className="flex flex-col gap-2">
                <label
                  htmlFor="custom-length"
                  className="text-sm font-medium"
                >
                  Overall Length
                </label>

                <div className="relative">
                  <input
                    id="custom-length"
                    type="number"
                    step="0.1"
                    min={
                      dimensionRanges?.min_length_m
                    }
                    max={
                      dimensionRanges?.max_length_m
                    }
                    value={customLength}
                    onChange={(event) => {
                      setCustomLength(
                        event.target.value
                      );
                      setResult(null);
                    }}
                    placeholder="Length"
                    className="h-10 w-full rounded-md border border-input bg-background px-3 pr-10 text-sm outline-none focus:ring-2 focus:ring-ring"
                  />

                  <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">
                    m
                  </span>
                </div>
              </div>
            </div>
          )}

        {/* Additional Questions */}
        {templateQuestions.length > 0 && (
          <div className="flex flex-col gap-4">
            <div>
              <h4 className="text-sm font-medium text-foreground">
                Additional Questions
              </h4>

              <p className="mt-1 text-xs text-muted-foreground">
                Additional information required for
                this vehicle type.
              </p>
            </div>

            {templateQuestions.map(
              (question) => {
                const answer =
                  extraAnswers[question.name];

                return (
                  <div
                    key={question.name}
                    className="flex flex-col gap-2"
                  >
                    <label
                      htmlFor={`question-${question.name}`}
                      className="text-sm font-medium"
                    >
                      {question.label}
                    </label>

                    {question.type === 'bool' ? (
                      <select
                        id={`question-${question.name}`}
                        value={
                          answer === true
                            ? 'true'
                            : answer === false
                              ? 'false'
                              : ''
                        }
                        onChange={(event) => {
                          handleExtraAnswer(
                            question,
                            event.target.value
                          );

                          setResult(null);
                          setError('');
                        }}
                        className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
                      >
                        <option value="">
                          — Select —
                        </option>

                        <option value="true">
                          Yes
                        </option>

                        <option value="false">
                          No
                        </option>
                      </select>
                    ) : (
                      <input
                        id={`question-${question.name}`}
                        type="number"
                        step="0.1"
                        value={
                          typeof answer ===
                            'string'
                            ? answer
                            : ''
                        }
                        onChange={(event) => {
                          handleExtraAnswer(
                            question,
                            event.target.value
                          );

                          setResult(null);
                          setError('');
                        }}
                        className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
                      />
                    )}
                  </div>
                );
              }
            )}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3">
            <p className="text-sm font-medium text-destructive">
              Unable to complete compliance check
            </p>

            <p className="mt-1 text-sm text-destructive">
              {error}
            </p>
          </div>
        )}

        {/* Actions */}
        {vehicleFormData && (
          <div className="flex flex-col gap-2 border-t border-border pt-5">
            <button
              type="button"
              onClick={classifyAndValidate}
              disabled={submitting}
              className="h-10 w-full rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {submitting
                ? 'Checking Compliance...'
                : 'Classify + Validate Mass'}
            </button>

            <button
              type="button"
              onClick={resetForm}
              disabled={submitting}
              className="h-10 w-full rounded-md border border-border bg-background px-4 text-sm font-medium transition-colors hover:bg-accent disabled:opacity-50"
            >
              Reset Form
            </button>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="flex flex-col gap-3 border-t border-border pt-5">
            <div>
              <h4 className="text-base font-semibold">
                Compliance Result
              </h4>

              <p className="mt-1 text-xs text-muted-foreground">
                Vehicle classification and mass
                validation.
              </p>
            </div>

            {/* Mass result */}
            <div
              className={
                result.mass_validation_result
                  .compliant
                  ? 'rounded-md border border-green-500/30 bg-green-500/10 p-4'
                  : 'rounded-md border border-destructive/30 bg-destructive/10 p-4'
              }
            >
              <div className="flex items-start gap-3">
                <div
                  className={
                    result.mass_validation_result
                      .compliant
                      ? 'flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-green-600 text-sm font-bold text-white'
                      : 'flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-destructive text-sm font-bold text-white'
                  }
                >
                  {result.mass_validation_result
                    .compliant
                    ? '✓'
                    : '!'}
                </div>

                <div>
                  <p className="text-sm font-semibold">
                    {result
                      .mass_validation_result
                      .compliant
                      ? 'Mass Compliant'
                      : 'Mass Not Compliant'}
                  </p>

                  <p className="mt-1 text-xs text-muted-foreground">
                    {
                      result
                        .mass_validation_result
                        .reason
                    }
                  </p>
                </div>
              </div>
            </div>

            {/* Classification */}
            <div
              className={
                classificationIsPass(
                  result.classification_result
                    .classification
                )
                  ? 'rounded-md border border-green-500/30 bg-green-500/10 p-4'
                  : result.classification_result
                    .classification ===
                    'class_3'
                    ? 'rounded-md border border-amber-500/30 bg-amber-500/10 p-4'
                    : 'rounded-md border border-destructive/30 bg-destructive/10 p-4'
              }
            >
              <div className="flex items-start gap-3">
                <div
                  className={
                    classificationIsPass(
                      result
                        .classification_result
                        .classification
                    )
                      ? 'flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-green-600 text-sm font-bold text-white'
                      : result
                        .classification_result
                        .classification ===
                        'class_3'
                        ? 'flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-amber-500 text-sm font-bold text-white'
                        : 'flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-destructive text-sm font-bold text-white'
                  }
                >
                  {classificationIsPass(
                    result.classification_result
                      .classification
                  )
                    ? '✓'
                    : '!'}
                </div>

                <div>
                  <p className="text-sm font-semibold">
                    Category:{' '}
                    {formatClassification(
                      result
                        .classification_result
                        .classification
                    )}
                  </p>

                  <p className="mt-1 text-xs text-muted-foreground">
                    {
                      result
                        .classification_result
                        .reason
                    }
                  </p>
                </div>
              </div>
            </div>

            {/* Warnings */}
            {result.classification_result
              .warnings.length > 0 && (
                <div className="rounded-md border border-amber-500/30 bg-amber-500/10 p-3">
                  <p className="text-sm font-medium">
                    Warnings
                  </p>

                  <ul className="mt-2 list-disc space-y-1 pl-4 text-xs text-muted-foreground">
                    {result.classification_result.warnings.map(
                      (warning, index) => (
                        <li key={index}>
                          {warning}
                        </li>
                      )
                    )}
                  </ul>
                </div>
              )}
          </div>
        )}
      </div>
    </div>
  );
};