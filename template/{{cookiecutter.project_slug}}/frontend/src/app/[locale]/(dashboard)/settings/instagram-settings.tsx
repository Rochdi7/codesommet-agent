{%- if cookiecutter.enable_instagram %}
{% raw %}"use client";

import { useCallback, useEffect, useState } from "react";
import { Card, Badge, Button, Input, Label, Switch } from "@/components/ui";
import { Instagram, Eye, EyeOff, CheckCircle, XCircle, Loader2, Save, FlaskConical } from "lucide-react";
import { apiClient } from "@/lib/api-client";

interface SettingsData {
  id: string;
  page_id: string | null;
  page_access_token_set: boolean;
  app_secret_set: boolean;
  webhook_verify_token: string | null;
  auto_reply: boolean;
  created_at: string;
  updated_at: string | null;
}

interface TestLog {
  field: string;
  status: "ok" | "error" | "skip";
  message: string;
  detail: string | null;
}

interface TestResult {
  success: boolean;
  logs: TestLog[];
  page_name: string | null;
  instagram_business_account_id: string | null;
}

export function InstagramSettings() {
  const [settings, setSettings] = useState<SettingsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Form fields
  const [pageId, setPageId] = useState("");
  const [pageAccessToken, setPageAccessToken] = useState("");
  const [appSecret, setAppSecret] = useState("");
  const [webhookVerifyToken, setWebhookVerifyToken] = useState("");
  const [autoReply, setAutoReply] = useState(false);

  // Visibility toggles for sensitive fields
  const [showToken, setShowToken] = useState(false);
  const [showSecret, setShowSecret] = useState(false);

  const [isEditing, setIsEditing] = useState(false);

  const fetchSettings = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiClient.get<SettingsData>("/v1/instagram/settings");
      setSettings(data);
      setPageId(data.page_id || "");
      setWebhookVerifyToken(data.webhook_verify_token || "");
      setAutoReply(data.auto_reply);
      // Don't populate sensitive fields — they come as booleans
      setPageAccessToken("");
      setAppSecret("");
    } catch {
      setError("Failed to load Instagram settings");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccessMsg(null);
      setTestResult(null);

      const body: Record<string, unknown> = {
        page_id: pageId || null,
        webhook_verify_token: webhookVerifyToken || null,
        auto_reply: autoReply,
      };

      // Only send sensitive fields if user typed something new
      if (pageAccessToken) {
        body.page_access_token = pageAccessToken;
      }
      if (appSecret) {
        body.app_secret = appSecret;
      }

      const data = await apiClient.put<SettingsData>("/v1/instagram/settings", body);
      setSettings(data);
      setPageAccessToken("");
      setAppSecret("");
      setIsEditing(false);
      setSuccessMsg("Settings saved successfully");
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch {
      setError("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    try {
      setTesting(true);
      setError(null);
      setTestResult(null);
      const result = await apiClient.post<TestResult>("/v1/instagram/test");
      setTestResult(result);
    } catch {
      setError("Failed to test connection");
    } finally {
      setTesting(false);
    }
  };

  if (loading) {
    return (
      <Card className="p-4 sm:p-6">
        <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold">
          <Instagram className="h-5 w-5" />
          Instagram Integration
        </h3>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          <span className="ml-2 text-sm text-muted-foreground">Loading settings...</span>
        </div>
      </Card>
    );
  }

  const hasSettings = settings && settings.id;

  return (
    <Card className="p-4 sm:p-6">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="flex items-center gap-2 text-lg font-semibold">
          <Instagram className="h-5 w-5" />
          Instagram Integration
        </h3>
        <div className="flex items-center gap-2">
          {hasSettings && !isEditing && (
            <Button variant="outline" size="sm" onClick={() => setIsEditing(true)}>
              Edit
            </Button>
          )}
          {!hasSettings && !isEditing && (
            <Button variant="outline" size="sm" onClick={() => setIsEditing(true)}>
              Configure
            </Button>
          )}
        </div>
      </div>

      {error && (
        <div className="mb-4 rounded-md border border-destructive/50 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </div>
      )}

      {successMsg && (
        <div className="mb-4 rounded-md border border-green-500/50 bg-green-500/10 px-3 py-2 text-sm text-green-700 dark:text-green-400">
          {successMsg}
        </div>
      )}

      {/* View mode — show stored data */}
      {!isEditing && (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Page ID</span>
            <span className="font-mono text-xs">
              {settings?.page_id || <span className="text-muted-foreground italic">Not set</span>}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Page Access Token</span>
            <Badge variant={settings?.page_access_token_set ? "default" : "secondary"}>
              {settings?.page_access_token_set ? "Set" : "Not set"}
            </Badge>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">App Secret</span>
            <Badge variant={settings?.app_secret_set ? "default" : "secondary"}>
              {settings?.app_secret_set ? "Set" : "Not set"}
            </Badge>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Webhook Verify Token</span>
            <span className="font-mono text-xs">
              {settings?.webhook_verify_token || <span className="text-muted-foreground italic">Not set</span>}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Auto Reply</span>
            <Badge variant={settings?.auto_reply ? "default" : "outline"}>
              {settings?.auto_reply ? "Enabled" : "Disabled"}
            </Badge>
          </div>

          {settings?.updated_at && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Last Updated</span>
              <span className="text-xs text-muted-foreground">
                {new Date(settings.updated_at).toLocaleString()}
              </span>
            </div>
          )}

          {/* Test connection button */}
          {hasSettings && (
            <div className="pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleTest}
                disabled={testing}
                className="w-full"
              >
                {testing ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <FlaskConical className="mr-2 h-4 w-4" />
                )}
                {testing ? "Testing..." : "Test Connection"}
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Edit mode — form */}
      {isEditing && (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="ig-page-id">Page ID</Label>
            <Input
              id="ig-page-id"
              value={pageId}
              onChange={(e) => setPageId(e.target.value)}
              placeholder="e.g. 123456789012345"
            />
            <p className="text-xs text-muted-foreground">
              Your Facebook Page ID from Meta Developer Dashboard
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="ig-token">Page Access Token</Label>
            <div className="relative">
              <Input
                id="ig-token"
                type={showToken ? "text" : "password"}
                value={pageAccessToken}
                onChange={(e) => setPageAccessToken(e.target.value)}
                placeholder={settings?.page_access_token_set ? "(unchanged — enter new value to update)" : "Paste long-lived token"}
                className="pr-10"
              />
              <button
                type="button"
                onClick={() => setShowToken(!showToken)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showToken ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="ig-secret">App Secret</Label>
            <div className="relative">
              <Input
                id="ig-secret"
                type={showSecret ? "text" : "password"}
                value={appSecret}
                onChange={(e) => setAppSecret(e.target.value)}
                placeholder={settings?.app_secret_set ? "(unchanged — enter new value to update)" : "From Meta App Settings > Basic"}
                className="pr-10"
              />
              <button
                type="button"
                onClick={() => setShowSecret(!showSecret)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showSecret ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="ig-verify">Webhook Verify Token</Label>
            <Input
              id="ig-verify"
              value={webhookVerifyToken}
              onChange={(e) => setWebhookVerifyToken(e.target.value)}
              placeholder="Any custom string (must match Meta webhook config)"
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <Label htmlFor="ig-auto-reply">Auto Reply</Label>
              <p className="text-xs text-muted-foreground">Automatically respond to incoming DMs</p>
            </div>
            <Switch
              id="ig-auto-reply"
              checked={autoReply}
              onCheckedChange={setAutoReply}
            />
          </div>

          <div className="flex gap-2 pt-2">
            <Button onClick={handleSave} disabled={saving} className="flex-1">
              {saving ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Save className="mr-2 h-4 w-4" />
              )}
              {saving ? "Saving..." : "Save Settings"}
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setIsEditing(false);
                setError(null);
                // Reset form to stored values
                if (settings) {
                  setPageId(settings.page_id || "");
                  setWebhookVerifyToken(settings.webhook_verify_token || "");
                  setAutoReply(settings.auto_reply);
                  setPageAccessToken("");
                  setAppSecret("");
                }
              }}
            >
              Cancel
            </Button>
          </div>
        </div>
      )}

      {/* Test results */}
      {testResult && (
        <div className="mt-4 space-y-2 rounded-md border p-3">
          <div className="flex items-center justify-between text-sm font-medium">
            <span>Connection Test Results</span>
            <Badge variant={testResult.success ? "default" : "destructive"}>
              {testResult.success ? "All Passed" : "Issues Found"}
            </Badge>
          </div>
          {testResult.page_name && (
            <p className="text-xs text-muted-foreground">
              Page: {testResult.page_name}
              {testResult.instagram_business_account_id && (
                <> &middot; IG Account: {testResult.instagram_business_account_id}</>
              )}
            </p>
          )}
          <div className="space-y-1">
            {testResult.logs.map((log, i) => (
              <div key={i} className="flex items-start gap-2 text-xs">
                {log.status === "ok" ? (
                  <CheckCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-green-500" />
                ) : (
                  <XCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-destructive" />
                )}
                <div>
                  <span className={log.status === "ok" ? "text-foreground" : "text-destructive"}>
                    {log.message}
                  </span>
                  {log.detail && (
                    <p className="text-muted-foreground mt-0.5">{log.detail}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}{% endraw %}
{%- endif %}
