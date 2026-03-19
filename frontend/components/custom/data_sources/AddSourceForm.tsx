"use client";

import { useState } from "react";

export default function AddSourceForm() {
  const [form, setForm] = useState({
    name: "",
    source_type: "postgres",
    host: "",
    port: "",
    source_name: "",
    username: "",
    password: "",
  });

  const [loading, setLoading] = useState(false);

  const handleChange = (e: any) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async () => {
    setLoading(true);

    const payload = {
      name: form.name,
      source_type: form.source_type,
      host: form.host || null,
      port: form.port ? Number(form.port) : null,
      source_name: form.source_name || null,
      metadata: {
        username: form.username,
        password: form.password,
      },
    };

    try {
      const res = await fetch("http://localhost:8080/api/add_source", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error("Failed");

      alert("✅ Source added!");

      // reset form
      setForm({
        name: "",
        source_type: "postgres",
        host: "",
        port: "",
        source_name: "",
        username: "",
        password: "",
      });
    } catch (err) {
      console.error(err);
      alert("❌ Error adding source");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-3 border p-4 rounded-xl">
      <h3 className="font-semibold">Add New Source</h3>

      <input
        name="name"
        placeholder="Source Name"
        value={form.name}
        onChange={handleChange}
        className="border p-2 rounded"
      />

      <select
        name="source_type"
        value={form.source_type}
        onChange={handleChange}
        className="border p-2 rounded"
      >
        <option value="postgres">Postgres</option>
        <option value="mysql">MySQL</option>
        <option value="mongodb">MongoDB</option>
        <option value="s3">S3 (future)</option>
      </select>

      {/* DB Fields (only for now) */}
      <input
        name="host"
        placeholder="Host"
        value={form.host}
        onChange={handleChange}
        className="border p-2 rounded"
      />

      <input
        name="port"
        placeholder="Port"
        value={form.port}
        onChange={handleChange}
        className="border p-2 rounded"
      />

      <input
        name="source_name"
        placeholder="Database Name"
        value={form.source_name}
        onChange={handleChange}
        className="border p-2 rounded"
      />

      <input
        name="username"
        placeholder="Username"
        value={form.username}
        onChange={handleChange}
        className="border p-2 rounded"
      />

      <input
        name="password"
        type="password"
        placeholder="Password"
        value={form.password}
        onChange={handleChange}
        className="border p-2 rounded"
      />

      <button
        onClick={handleSubmit}
        disabled={loading}
        className="bg-black text-white p-2 rounded"
      >
        {loading ? "Adding..." : "Add Source"}
      </button>
    </div>
  );
}
