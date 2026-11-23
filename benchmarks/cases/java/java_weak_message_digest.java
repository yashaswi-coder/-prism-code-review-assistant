import java.security.MessageDigest;

class WeakDigestCase {
    byte[] hash(byte[] input) throws Exception {
        return MessageDigest.getInstance("MD5").digest(input);
    }
}
