/** Public API of the auth feature (M1). Other features import only from "@/features/auth". */
export { AuthMenu } from "./components/AuthMenu";
export { LoginForm } from "./components/LoginForm";
export { RegisterForm } from "./components/RegisterForm";
export { RequireAuthProvider, useRequireAuth } from "./components/RequireAuth";
export { useLogin, useLogout, useRegister } from "./hooks/useAuthMutations";
export { safeNext } from "./validation";
export { ME_QUERY_KEY, type Me, useMe } from "./hooks/useMe";
